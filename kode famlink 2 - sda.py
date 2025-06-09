import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import json
from PIL import Image, ImageTk
import os

class Node:
    def __init__(self, pasangan):
        self.pasangan = pasangan  # tuple (nama1, nama2) bisa kosong salah satu ''
        self.anak = []
        self.x = 0
        self.y = 0
        self.canvas_x = 0
        self.canvas_y = 0

class PohonKeluarga:
    def __init__(self):
        self.root = None
        self.nodes = []

    def tambah_akar(self, pasangan):
        self.root = Node(pasangan)
        self.nodes = [self.root]

    def tambah_anak(self, node, pasangan_anak):
        anak = Node(pasangan_anak)
        node.anak.append(anak)
        self.nodes.append(anak)

    def simpan(self, nama_file):
        def node_ke_dict(node):
            return {
                'pasangan': node.pasangan,
                'x': node.x,
                'y': node.y,
                'anak': [node_ke_dict(a) for a in node.anak]
            }
        with open(nama_file, 'w') as f:
            json.dump(node_ke_dict(self.root), f)

    def muat(self, nama_file):
        def dict_ke_node(data):
            node = Node(data['pasangan'])
            node.x = data.get('x', 0)
            node.y = data.get('y', 0)
            node.anak = [dict_ke_node(a) for a in data['anak']]
            return node
        with open(nama_file, 'r') as f:
            data = json.load(f)
            self.root = dict_ke_node(data)
            self.nodes = []
            self._kumpulkan_node(self.root)

    def _kumpulkan_node(self, node):
        self.nodes.append(node)
        for anak in node.anak:
            self._kumpulkan_node(anak)

    def layout(self):
        def atur_posisi(node, depth, posisi_x):
            node.y = depth * 100 + 50
            if not node.anak:
                node.x = posisi_x[0]
                posisi_x[0] += 250
            else:
                for anak in node.anak:
                    atur_posisi(anak, depth + 1, posisi_x)
                node.x = sum(a.x for a in node.anak) // len(node.anak)

        posisi_x = [100]
        if self.root:
            atur_posisi(self.root, 0, posisi_x)

class GenderInputDialog:
    def __init__(self, parent, title, label):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.value = None
        self.gender = None

        tk.Label(self.top, text=label).pack(pady=5)
        self.entry = tk.Entry(self.top)
        self.entry.pack(pady=5)

        gender_frame = tk.Frame(self.top)
        gender_frame.pack(pady=5)
        tk.Button(gender_frame, text="Laki-laki", command=self.set_male).pack(side=tk.LEFT, padx=5)
        tk.Button(gender_frame, text="Perempuan", command=self.set_female).pack(side=tk.LEFT, padx=5)

    def set_male(self):
        self.value = (self.entry.get(), 'laki-laki')
        self.top.destroy()

    def set_female(self):
        self.value = (self.entry.get(), 'perempuan')
        self.top.destroy()

class PohonKeluargaApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Pohon Keluarga')
        self.pohon = PohonKeluarga()

        # Frame atas untuk tombol-tombol
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        def buat_tombol(text, command, bg_color):
            lbl = tk.Label(button_frame, text=text, bg=bg_color, fg='white', padx=10, pady=5, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<Button-1>", lambda e: command())
            return lbl

        # Buat semua tombol dengan warna
        buat_tombol('Tambah Orangtua', self.tambah_akar, '#145A32')
        buat_tombol('Tambah Anak', self.tambah_anak, '#27ae60')
        buat_tombol('Tambah Pasangan', self.tambah_pasangan, '#556B2F')
        buat_tombol('Hapus Anggota', self.hapus_node, '#A1866F')
        buat_tombol('Simpan', self.simpan, '#006400')
        buat_tombol('Muat', self.muat, '#3E2723')
        buat_tombol('Toggle Fixed Layout', self.toggle_fixed_layout, '#5D4037')

        # Frame bawah untuk canvas dan scrollbar
        canvas_frame = tk.Frame(root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='#FFF5E1', scrollregion=(0, 0, 15000, 9000))
        self.canvas.grid(row=0, column=0, sticky='nsew')

        self.bg_image = Image.open("pohon.png")  # Ganti dengan nama file PNG kamu
        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)

        # Tambahkan ke canvas sebagai background (gunakan tag 'bg' supaya mudah kelola)
        self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor='nw', tags='bg')

        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky='ns')

        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky='ew')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.node_terpilih = None
        self.fixed_layout = False
        self.drag_data = {"x": 0, "y": 0, "node": None}
        self.scale = 1.0

        self.canvas.bind("<Button-1>", self.pilih_node)
        self.canvas.bind("<B1-Motion>", self.drag_node)
        self.canvas.bind("<ButtonRelease-1>", self.release_node)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.do_pan)

    def dialog_dengan_gender(self, judul, label):
        dialog = GenderInputDialog(self.root, judul, label)
        self.root.wait_window(dialog.top)
        if dialog.value:
            return f"{dialog.value[0].strip()} ({dialog.value[1]})"
        return None

    def tambah_akar(self):
        nama1 = self.dialog_dengan_gender("Pasangan 1", "Nama Pasangan 1:")
        if not nama1:
            return
        nama2 = self.dialog_dengan_gender("Pasangan 2", "Nama Pasangan 2:")
        if not nama2:
            return
        self.pohon.tambah_akar((nama1, nama2))
        self.update_canvas()

    def tambah_anak(self):
        if not self.node_terpilih:
            messagebox.showwarning("Peringatan", "Pilih node (orang tua) terlebih dahulu.")
            return
        nama = self.dialog_dengan_gender("Tambah Anak", "Nama Anak:")
        if not nama:
            return
        self.pohon.tambah_anak(self.node_terpilih, (nama, ''))
        self.update_canvas()

    def tambah_pasangan(self):
        if not self.node_terpilih:
            messagebox.showwarning("Peringatan", "Pilih node yang ingin ditambah pasangan.")
            return

        pasangan_baru = self.dialog_dengan_gender("Tambah Pasangan", "Nama Pasangan:")
        if not pasangan_baru:
            return

        nama1, nama2 = self.node_terpilih.pasangan
        if nama1 == '':
            nama1 = pasangan_baru
        elif nama2 == '':
            nama2 = pasangan_baru
        else:
            messagebox.showinfo("Info", "Node sudah memiliki pasangan lengkap.")
            return

        self.node_terpilih.pasangan = (nama1, nama2)
        self.update_canvas()

    def hapus_node(self):
        if not self.node_terpilih:
            messagebox.showwarning("Peringatan", "Pilih node yang akan dihapus terlebih dahulu.")
            return

        if self.node_terpilih == self.pohon.root:
            confirm = messagebox.askyesno("Konfirmasi", "Anda akan menghapus akar dan seluruh pohon. Lanjutkan?")
            if confirm:
                self.pohon.root = None
                self.pohon.nodes = []
                self.node_terpilih = None
                self.update_canvas()
            return

        def hapus_dari_parent(node, target):
            if target in node.anak:
                node.anak.remove(target)
                return True
            for anak in node.anak:
                if hapus_dari_parent(anak, target):
                    return True
            return False

        hapus_dari_parent(self.pohon.root, self.node_terpilih)

        def hapus_semua_descendant(node):
            for anak in node.anak:
                hapus_semua_descendant(anak)
            if node in self.pohon.nodes:
                self.pohon.nodes.remove(node)

        hapus_semua_descendant(self.node_terpilih)
        if self.node_terpilih in self.pohon.nodes:
            self.pohon.nodes.remove(self.node_terpilih)

        self.node_terpilih = None
        self.update_canvas()

    def simpan(self):
        file = filedialog.asksaveasfilename(defaultextension=".json")
        if file:
            self.pohon.simpan(file)

    def muat(self):
        file = filedialog.askopenfilename(defaultextension=".json")
        if file:
            self.pohon.muat(file)
            self.update_canvas()

    def toggle_fixed_layout(self):
        self.fixed_layout = not self.fixed_layout
        mode = "aktif" if self.fixed_layout else "non-aktif"
        messagebox.showinfo("Layout Tetap", f"Mode layout tetap sekarang {mode}.")
        self.update_canvas()

    def update_canvas(self):
        self.canvas.delete('all')

        if os.path.exists("pohon.png"):
            self.bg_image = Image.open("pohon.png")
            self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)
            self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor='nw', tags='bg')
        else:
            messagebox.showerror("Gambar Tidak Ditemukan", "File pohon.png tidak ditemukan. Pastikan file ada di folder yang sama.")

        if not self.fixed_layout:
            self.pohon.layout()

        def bersih(n):
            return n.replace(' (laki-laki)', '').replace(' (perempuan)', '')

        for node in self.pohon.nodes:
            x, y = node.x * self.scale, node.y * self.scale
            w, h = 120 * self.scale, 40 * self.scale
            node.canvas_x, node.canvas_y = x, y

            nama1, nama2 = node.pasangan
            if nama1 and nama2:
                x_offset = 60 * self.scale
                warna1 = '#ADD8E6' if '(laki-laki)' in nama1 else '#FFB6C1' if '(perempuan)' in nama1 else '#D3D3D3'
                warna2 = '#ADD8E6' if '(laki-laki)' in nama2 else '#FFB6C1' if '(perempuan)' in nama2 else '#D3D3D3'
                if node == self.node_terpilih:
                    warna1 = warna2 = 'orange'

                rect1 = self.canvas.create_rectangle(x - x_offset - w//2, y - h//2, x - x_offset + w//2, y + h//2, fill=warna1)
                rect2 = self.canvas.create_rectangle(x + x_offset - w//2, y - h//2, x + x_offset + w//2, y + h//2, fill=warna2)

                self.canvas.create_text(x - x_offset, y, text=bersih(nama1), font=('Arial', int(12 * self.scale)))
                self.canvas.create_text(x + x_offset, y, text=bersih(nama2), font=('Arial', int(12 * self.scale)))

                self.canvas.create_line(x - x_offset + w//2, y, x + x_offset - w//2, y, fill='black', width=2)
            else:
                nama_tampil = bersih(nama1 if nama1 else nama2)
                warna = '#ADD8E6' if '(laki-laki)' in (nama1 + nama2) else '#FFB6C1' if '(perempuan)' in (nama1 + nama2) else '#D3D3D3'
                if node == self.node_terpilih:
                    warna = 'orange'
                rect = self.canvas.create_rectangle(x - w//2, y - h//2, x + w//2, y + h//2, fill=warna)
                self.canvas.create_text(x, y, text=nama_tampil, font=('Arial', int(12 * self.scale)))

        # Gambar garis dari orang tua ke anak hanya ke kotak anak saja
        for node in self.pohon.nodes:
            for anak in node.anak:
                # x1, y1 = node.canvas_x, node.canvas_y + (20 * self.scale)
                x1 = node.x * self.scale
                y1 = node.y * self.scale + (20 * self.scale)
                # Tentukan posisi target garis di anak:
                # Jika anak punya pasangan dua orang, arahkan ke kotak pasangan 1 (kiri)
                offset = 5
                if anak.pasangan[1] != '':
                    target_x = (anak.x - 60 - offset) * self.scale
                else:
                    target_x = anak.x * self.scale
                y2 = anak.y * self.scale - (20 * self.scale)

                self.canvas.create_line(x1, y1, target_x, y2, width=2)

        # Gambar garis pasangan
        for node in self.pohon.nodes:
            nama1, nama2 = node.pasangan
            if nama1 and nama2 and nama1 != '' and nama2 != '':
                x, y = node.canvas_x, node.canvas_y
                x_offset = 60 * self.scale
                self.canvas.create_line(x - x_offset + 60, y, x + x_offset - 60, y, fill='black', width=2)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.bg_image_id = self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor='nw', tags='bg')
        self.canvas.tag_lower('bg')
        
    def pilih_node(self, event):
        x, y = event.x / self.scale, event.y / self.scale
        terdekat = None
        jarak_terdekat = 9999

        for node in self.pohon.nodes:
            nx, ny = node.x, node.y
            jarak = (nx - x) ** 2 + (ny - y) ** 2
            if jarak < jarak_terdekat and jarak < 60 ** 2:
                terdekat = node
                jarak_terdekat = jarak

        self.node_terpilih = terdekat
        self.update_canvas()

        if terdekat:
            self.drag_data["node"] = terdekat
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def drag_node(self, event):
        if self.fixed_layout:
            return
        node = self.drag_data["node"]
        if node:
            dx = (event.x - self.drag_data["x"]) / self.scale
            dy = (event.y - self.drag_data["y"]) / self.scale
            node.x += dx
            node.y += dy
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.update_canvas()

    def release_node(self, event):
        self.drag_data["node"] = None

    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self.update_canvas()

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1430x1024")
    app = PohonKeluargaApp(root)
    root.mainloop()
