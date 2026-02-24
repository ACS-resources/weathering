from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List

from planet_info import (
    PLANET_TYPES,
    STAR_TYPES,
    GalaxyRecord,
    PlanetRecord,
    StarSystemRecord,
    export_planet_preview,
    filter_planets,
    iter_galaxies,
    iter_planets,
    iter_star_systems,
    sort_planets,
)


class ExplorerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weathering 宇宙信息筛选器")
        self.geometry("1400x820")

        self.galaxies = list(iter_galaxies())
        self.star_cache: Dict[tuple, List[StarSystemRecord]] = {}
        self.planet_cache: Dict[tuple, List[PlanetRecord]] = {}
        self.current_planets: List[PlanetRecord] = []
        self.selected_planet: PlanetRecord | None = None

        self._build_ui()
        self._load_tree_root()

    def _build_ui(self) -> None:
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=6)
        right = ttk.Frame(paned, padding=6)
        paned.add(left, weight=2)
        paned.add(right, weight=3)

        self.tree = ttk.Treeview(left, columns=("kind", "pos"), show="tree headings")
        self.tree.heading("#0", text="宇宙层级")
        self.tree.heading("kind", text="类型")
        self.tree.heading("pos", text="坐标")
        self.tree.column("kind", width=90, anchor=tk.CENTER)
        self.tree.column("pos", width=130, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        filter_box = ttk.LabelFrame(right, text="查询 / 筛选 / 排序", padding=8)
        filter_box.pack(fill=tk.X)

        self.filter_planet_type = tk.StringVar(value="")
        self.filter_star_type = tk.StringVar(value="")
        self.sort_by = tk.StringVar(value="planet_size")
        self.sort_desc = tk.BooleanVar(value=True)

        row1 = ttk.Frame(filter_box)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="行星类型").pack(side=tk.LEFT)
        ttk.Combobox(row1, textvariable=self.filter_planet_type, values=[""] + sorted(PLANET_TYPES.values()), width=14).pack(side=tk.LEFT, padx=4)
        ttk.Label(row1, text="恒星类型").pack(side=tk.LEFT)
        ttk.Combobox(row1, textvariable=self.filter_star_type, values=[""] + [STAR_TYPES[k] for k in sorted(STAR_TYPES)], width=10).pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(filter_box)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="排序字段").pack(side=tk.LEFT)
        ttk.Combobox(row2, textvariable=self.sort_by, values=["planet_size", "mineral_density", "seconds_for_a_day", "days_for_a_year"], width=18).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(row2, text="降序", variable=self.sort_desc).pack(side=tk.LEFT, padx=8)
        ttk.Button(row2, text="应用", command=self._apply_filter_sort).pack(side=tk.LEFT, padx=4)

        columns = ("map_key", "star", "ptype", "size", "day", "year", "mineral")
        self.table = ttk.Treeview(right, columns=columns, show="headings", height=18)
        for c, t, w in [
            ("map_key", "MapKey", 380),
            ("star", "恒星", 90),
            ("ptype", "行星", 100),
            ("size", "大小", 70),
            ("day", "昼夜(s)", 80),
            ("year", "四季(天)", 80),
            ("mineral", "矿物稀疏度", 100),
        ]:
            self.table.heading(c, text=t)
            self.table.column(c, width=w, anchor=tk.CENTER)
        self.table.pack(fill=tk.BOTH, expand=True, pady=8)
        self.table.bind("<<TreeviewSelect>>", self._on_table_select)

        detail = ttk.LabelFrame(right, text="详情", padding=8)
        detail.pack(fill=tk.X)
        self.detail_text = tk.Text(detail, height=8)
        self.detail_text.pack(fill=tk.X)

        btn_row = ttk.Frame(right)
        btn_row.pack(fill=tk.X, pady=6)
        ttk.Button(btn_row, text="导出当前选中星球预览", command=self._export_preview).pack(side=tk.LEFT)

    def _load_tree_root(self) -> None:
        root = self.tree.insert("", tk.END, iid="universe", text="宇宙", values=("MapOfUniverse", "100x100"))
        for g in self.galaxies:
            gid = f"g:{g.pos[0]},{g.pos[1]}"
            self.tree.insert(root, tk.END, iid=gid, text=f"银河系 {g.pos}", values=("MapOfGalaxy", str(g.pos)))

    def _on_expand(self, _event) -> None:
        iid = self.tree.focus()
        if iid.startswith("g:"):
            gx, gy = map(int, iid[2:].split(","))
            galaxy = (gx, gy)
            if galaxy not in self.star_cache:
                self.star_cache[galaxy] = list(iter_star_systems(galaxy))
            if not self.tree.get_children(iid):
                for s in self.star_cache[galaxy]:
                    sid = f"s:{gx},{gy}:{s.pos[0]},{s.pos[1]}"
                    self.tree.insert(iid, tk.END, iid=sid, text=f"恒星系 {s.pos}", values=(s.star_type, s.pos))
        elif iid.startswith("s:"):
            gseg, sseg = iid[2:].split(":")
            gx, gy = map(int, gseg.split(","))
            sx, sy = map(int, sseg.split(","))
            key = (gx, gy, sx, sy)
            if key not in self.planet_cache:
                srec = StarSystemRecord((gx, gy), (sx, sy), "", "")
                self.planet_cache[key] = list(iter_planets(srec))
            if not self.tree.get_children(iid):
                for p in self.planet_cache[key]:
                    pid = f"p:{gx},{gy}:{sx},{sy}:{p.planet_pos[0]},{p.planet_pos[1]}"
                    self.tree.insert(iid, tk.END, iid=pid, text=f"{p.planet_type} {p.planet_pos}", values=("MapOfPlanet", p.planet_pos))

    def _on_select(self, _event) -> None:
        iid = self.tree.focus()
        self.current_planets.clear()
        if iid.startswith("s:"):
            gseg, sseg = iid[2:].split(":")
            gx, gy = map(int, gseg.split(","))
            sx, sy = map(int, sseg.split(","))
            key = (gx, gy, sx, sy)
            if key not in self.planet_cache:
                self.planet_cache[key] = list(iter_planets(StarSystemRecord((gx, gy), (sx, sy), "", "")))
            self.current_planets = list(self.planet_cache[key])
            self._apply_filter_sort()

    def _apply_filter_sort(self) -> None:
        filtered = filter_planets(
            self.current_planets,
            planet_type=self.filter_planet_type.get() or None,
            star_type=self.filter_star_type.get() or None,
        )
        sorted_items = sort_planets(filtered, self.sort_by.get(), self.sort_desc.get())
        for item in self.table.get_children():
            self.table.delete(item)
        for i, p in enumerate(sorted_items):
            self.table.insert("", tk.END, iid=f"row:{i}", values=(p.map_key, p.star_type, p.planet_type, p.planet_size, p.seconds_for_a_day, p.days_for_a_year, p.mineral_density))

    def _on_table_select(self, _event) -> None:
        sel = self.table.focus()
        if not sel:
            return
        idx = int(sel.split(":")[1])
        filtered = filter_planets(
            self.current_planets,
            planet_type=self.filter_planet_type.get() or None,
            star_type=self.filter_star_type.get() or None,
        )
        sorted_items = sort_planets(filtered, self.sort_by.get(), self.sort_desc.get())
        if idx >= len(sorted_items):
            return
        p = sorted_items[idx]
        self.selected_planet = p
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(
            tk.END,
            f"MapKey: {p.map_key}\n"
            f"恒星类型: {p.star_type}\n"
            f"行星类型: {p.planet_type}\n"
            f"昼夜周期: {p.seconds_for_a_day}s\n"
            f"四季周期: {p.days_for_a_year}天\n"
            f"月相周期: {p.days_for_a_month}天\n"
            f"四季月相: {p.month_for_a_year}个月\n"
            f"星球大小: {p.planet_size}\n"
            f"矿物稀疏度: {p.mineral_density}\n"
        )

    def _export_preview(self) -> None:
        if not self.selected_planet:
            messagebox.showwarning("未选择", "请先在右侧表格选择一个星球")
            return
        file = filedialog.asksaveasfilename(
            title="导出预览",
            defaultextension=".png",
            initialfile=f"planet_{self.selected_planet.planet_pos[0]}_{self.selected_planet.planet_pos[1]}.png",
            filetypes=[("PNG", "*.png")],
        )
        if not file:
            return
        dst = export_planet_preview(self.selected_planet, Path(file))
        messagebox.showinfo("完成", f"导出成功: {dst}")


if __name__ == "__main__":
    ExplorerApp().mainloop()
