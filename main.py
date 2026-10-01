import os
import pandas as pd
from datetime import datetime

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconRightWidget

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class HeatingSpecApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        
        # State tracking
        self.items = []
        self.selected_category = ""
        self.selected_material = ""
        
        # Preset Database
        self.db = {
            "Panelni radijatori": [
                ("Panelni radijator Tip 22 600x800", 8200.0, "kom"),
                ("Panelni radijator Tip 22 600x1000", 9500.0, "kom"),
                ("Panelni radijator Tip 22 600x1200", 11000.0, "kom"),
            ],
            "Aluminijumski radijatori": [
                ("Aluminijumski clanak H350", 1200.0, "kom"),
                ("Aluminijumski clanak H500", 1450.0, "kom"),
                ("Aluminijumski clanak H600", 1600.0, "kom"),
            ],
            "Cevi i fitinzi": [
                ("Bakarne cevi Ø15x1mm", 450.0, "m"),
                ("Bakarne cevi Ø18x1mm", 580.0, "m"),
                ("Alpex cev Ø16x2mm", 120.0, "m"),
            ]
        }

        screen = MDScreen()
        main_layout = MDBoxLayout(orientation="vertical", padding=15, spacing=15)

        # Header
        main_layout.add_widget(MDLabel(
            text="🔥 Specifikacija Grejanja",
            font_style="H5",
            size_hint_y=None,
            height=30,
            halign="center"
        ))

        # Inputs: Client & Location
        self.client_input = MDTextField(hint_text="Investitor / Klijent", text="Petar Petrovic", size_hint_y=None, height=50)
        self.location_input = MDTextField(hint_text="Objekat / Lokacija", text="Porodicna kuca", size_hint_y=None, height=50)
        main_layout.add_widget(self.client_input)
        main_layout.add_widget(self.location_input)

        # Row 1: Dropdown Buttons
        btn_layout = MDBoxLayout(spacing=10, size_hint_y=None, height=50)
        self.cat_btn = MDRaisedButton(
            text="1. Izaberi Kategoriju", 
            size_hint=(0.5, 1),
            on_release=self.open_cat_menu
        )
        self.mat_btn = MDRaisedButton(
            text="2. Izaberi Stavku", 
            size_hint=(0.5, 1),
            on_release=self.open_mat_menu
        )
        btn_layout.add_widget(self.cat_btn)
        btn_layout.add_widget(self.mat_btn)
        main_layout.add_widget(btn_layout)

        # Row 2: Quantity and Add Button
        add_layout = MDBoxLayout(spacing=10, size_hint_y=None, height=50)
        self.qty_input = MDTextField(hint_text="Kolicina", text="1", input_filter="float", size_hint_x=0.4)
        add_btn = MDRaisedButton(
            text="Dodaj u listu", 
            size_hint=(0.6, 1),
            on_release=self.add_item
        )
        add_layout.add_widget(self.qty_input)
        add_layout.add_widget(add_btn)
        main_layout.add_widget(add_layout)

        # Scrollable List View
        scroll = MDScrollView()
        self.list_view = MDList()
        scroll.add_widget(self.list_view)
        main_layout.add_widget(scroll)

        # Total Price
        self.total_label = MDLabel(
            text="Ukupno bez PDV: 0.00 RSD",
            font_style="Subtitle1",
            size_hint_y=None,
            height=30,
            halign="right"
        )
        main_layout.add_widget(self.total_label)

        # PDF Export Button
        export_btn = MDRaisedButton(
            text="📄 Generisi PDF Ponudu",
            size_hint_y=None,
            height=50,
            pos_hint={"center_x": 0.5},
            on_release=self.generate_pdf
        )
        main_layout.add_widget(export_btn)

        screen.add_widget(main_layout)
        return screen

    def open_cat_menu(self, instance):
        menu_items = [
            {
                "text": cat, 
                "viewclass": "OneLineListItem", 
                "on_release": lambda x=cat: self.select_category(x)
            }
            for cat in self.db.keys()
        ]
        self.cat_menu = MDDropdownMenu(
            caller=instance, 
            items=menu_items, 
            width_mult=4
        )
        self.cat_menu.open()

    def select_category(self, cat_name):
        self.selected_category = cat_name
        self.cat_btn.text = cat_name
        self.cat_menu.dismiss()
        self.selected_material = None
        self.mat_btn.text = "2. Izaberi Stavku"

    def open_mat_menu(self, instance):
        if not self.selected_category:
            return
        materials = self.db[self.selected_category]
        menu_items = [
            {
                "text": f"{item[0]} ({item[1]} RSD)", 
                "viewclass": "OneLineListItem", 
                "on_release": lambda x=item: self.select_material(x)
            }
            for item in materials
        ]
        self.mat_menu = MDDropdownMenu(
            caller=instance, 
            items=menu_items, 
            width_mult=5
        )
        self.mat_menu.open()

    def select_material(self, item_tuple):
        self.selected_material = item_tuple
        self.mat_btn.text = item_tuple[0]
        self.mat_menu.dismiss()

    def add_item(self, instance):
        if not self.selected_material:
            return
        qty = float(self.qty_input.text) if self.qty_input.text else 1.0
        name, price, unit = self.selected_material
        total = qty * price

        item_data = {"name": name, "qty": qty, "unit": unit, "price": price, "total": total}
        self.items.append(item_data)
        
        list_item = TwoLineAvatarIconListItem(
            text=f"{name} (x{qty} {unit})",
            secondary_text=f"Ukupno: {total:,.2f} RSD"
        )
        btn_delete = IconRightWidget(icon="delete", on_release=lambda x, i=item_data, li=list_item: self.remove_item(i, li))
        list_item.add_widget(btn_delete)
        self.list_view.add_widget(list_item)

        self.update_totals()

    def remove_item(self, item_data, list_item):
        if item_data in self.items:
            self.items.remove(item_data)
        self.list_view.remove_widget(list_item)
        self.update_totals()

    def update_totals(self):
        grand_total = sum(i["total"] for i in self.items)
        self.total_label.text = f"Ukupno bez PDV: {grand_total:,.2f} RSD"

    def generate_pdf(self, instance):
        if not self.items:
            return

        filename = f"Specifikacija_{self.client_input.text.replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("<b>SPECIFIKACIJA GREJNIH INSTALACIJA</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Investitor:</b> {self.client_input.text}", styles['Normal']))
        elements.append(Paragraph(f"<b>Objekat:</b> {self.location_input.text}", styles['Normal']))
        elements.append(Paragraph(f"<b>Datum:</b> {datetime.now().strftime('%d.%m.%Y.')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        table_data = [["Naziv", "J.M.", "Kolicina", "Cena", "Ukupno"]]
        for i in self.items:
            table_data.append([i["name"], i["unit"], str(i["qty"]), f"{i['price']:.2f}", f"{i['total']:.2f}"])

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.teal),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t)
        
        doc.build(elements)
        print(f"PDF Output created at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    HeatingSpecApp().run()