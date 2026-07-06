
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QRadioButton, 
                             QButtonGroup, QFileDialog, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                             QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt
from ui.workers import Worker
from ui.AdjustableTextEdit import AdjustableTextEdit
import csv
import json

class DataTab(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.layout = QVBoxLayout()
        
        self.header_label = QLabel("Import Data")
        self.layout.addWidget(self.header_label)
        
        self.info_label = QLabel("Load data to label from a demo source or your own CSV.")
        self.layout.addWidget(self.info_label)

        self.scrape_btn = QPushButton("Load Demo Data (RealPython Jobs)")
        self.scrape_btn.clicked.connect(self.run_scraper)
        self.layout.addWidget(self.scrape_btn)
        
        self.import_btn = QPushButton("Import CSV File")
        self.import_btn.clicked.connect(self.run_import)
        self.layout.addWidget(self.import_btn)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)
        
        self.setLayout(self.layout)

        if self.service.has_data():
            self.lock_ui("Data already exists in this workspace.")

    def lock_ui(self, message):
        self.scrape_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.info_label.setText(f"{message}")
        self.info_label.setStyleSheet("color: gray;")
        self.scrape_btn.setText("Import Locked (Data Loaded)")
        self.import_btn.setText("Import Locked (Data Loaded)")

    def run_scraper(self):
        self.scrape_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.log_area.append("Fetching demo data...")
        
        task = lambda cb: self.service.perform_demo_scrape(cb)
        self.worker = Worker(task)
        self.worker.progress_signal.connect(self.log_area.append)
        self.worker.finished_signal.connect(self.on_scrape_done)
        self.worker.start()

    def on_scrape_done(self, msg):
        self.log_area.append(msg)
        if self.service.has_data():
            self.lock_ui("Import complete.")
        else:
            self.scrape_btn.setEnabled(True)
            self.import_btn.setEnabled(True)

    def run_import(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open CSV', '.', "CSV Files (*.csv)")
        if fname:
            res = self.service.import_csv(fname)
            self.log_area.append(res)
            
            if self.service.has_data():
                self.lock_ui("Import complete.")

class DataViewTab(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.current_rows = []
        
        layout = QVBoxLayout()
        
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Data Viewer"))
        
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.fetch_and_load)
        controls_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addWidget(QLabel("Sort Content By:"))
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Default (Source)")
        self.sort_combo.currentTextChanged.connect(self.apply_sort)
        controls_layout.addWidget(self.sort_combo)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def showEvent(self, event):
        self.fetch_and_load() 
        super().showEvent(event)
        
    def fetch_and_load(self):
        self.current_rows = self.service.get_all_data()
        self.update_sort_options()
        self.apply_sort()

    def update_sort_options(self):
        if not self.current_rows: return

        all_keys = set()
        for row in self.current_rows:
            meta = row.get('metadata', {})
            if meta:
                all_keys.update(meta.keys())
        
        sorted_keys = sorted(list(all_keys))
        
        current_selection = self.sort_combo.currentText()
        
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        self.sort_combo.addItem("Default (Source)")
        self.sort_combo.addItems(sorted_keys)
        
        index = self.sort_combo.findText(current_selection)
        if index >= 0:
            self.sort_combo.setCurrentIndex(index)
            
        self.sort_combo.blockSignals(False)

    def apply_sort(self):
        sort_key = self.sort_combo.currentText()
        
        if sort_key == "Default (Source)":
            self.current_rows.sort(key=lambda x: x['source'])
        else:
            def get_sort_val(row):
                meta = row.get('metadata', {})
                return str(meta.get(sort_key, "")).lower()
            
            self.current_rows.sort(key=get_sort_val)
            
        self.load_table()

    def load_table(self):
        self.table.setSortingEnabled(False)
        self.table.clear()
        
        if not self.current_rows:
            self.table.setRowCount(0)
            return

        all_label_keys = set()
        for r in self.current_rows:
            all_label_keys.update(r['labels'].keys())
        sorted_label_keys = sorted(list(all_label_keys))
        
        cols = ["Source", "Full Content"] + sorted_label_keys
        
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(len(self.current_rows))
        
        for i, row_data in enumerate(self.current_rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row_data['source'])))
            
            meta = row_data.get('metadata', {})
            if meta:
                lines = [f"{k}: {v}" for k, v in meta.items()]
                display_text = "\n".join(lines)
            else:
                display_text = row_data.get('content_preview', "")
            self.table.setItem(i, 1, QTableWidgetItem(display_text))
            
            for j, key in enumerate(sorted_label_keys):
                val = row_data['labels'].get(key, "-")
                self.table.setItem(i, 2 + j, QTableWidgetItem(str(val)))
        
        self.table.resizeRowsToContents()
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 400)
        header.setStretchLastSection(True)

    def export_to_csv(self):
        """Export all data with labels to CSV"""
        if not self.current_rows:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return
        
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            'Export to CSV', 
            'labeled_data.csv', 
            "CSV Files (*.csv)"
        )
        
        if not fname:
            return
        
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as csvfile:
                all_label_keys = set()
                all_meta_keys = set()
                
                for row in self.current_rows:
                    all_label_keys.update(row['labels'].keys())
                    meta = row.get('metadata', {})
                    if meta:
                        all_meta_keys.update(meta.keys())
                
                sorted_label_keys = sorted(list(all_label_keys))
                sorted_meta_keys = sorted(list(all_meta_keys))
                
                fieldnames = ['id', 'source'] + sorted_meta_keys + sorted_label_keys
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row_data in self.current_rows:
                    csv_row = {
                        'id': row_data['id'],
                        'source': row_data['source']
                    }
                    
                    meta = row_data.get('metadata', {})
                    for key in sorted_meta_keys:
                        csv_row[key] = meta.get(key, '')
                    
                    for key in sorted_label_keys:
                        csv_row[key] = row_data['labels'].get(key, '')
                    
                    writer.writerow(csv_row)
            
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Exported {len(self.current_rows)} rows to:\n{fname}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"Failed to export CSV:\n{str(e)}"
            )


class LabelingTab(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.current_data = None
        self.dynamic_widgets = {} 
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        
        config_frame = QFrame()
        config_frame.setFrameShape(QFrame.Shape.StyledPanel)

        c_layout = QVBoxLayout()
        c_layout.addWidget(QLabel("<b>Create New Label Schema:</b>"))
        
        h_row1 = QHBoxLayout()
        self.new_q_input = QLineEdit()
        self.new_q_input.setPlaceholderText("Question (e.g., Sentiment)")
        
        self.q_type_combo = QComboBox()
        self.q_type_combo.addItems(["Boolean (Yes/No)", "Categorical (Multi-Options)"])
        self.q_type_combo.currentIndexChanged.connect(self.toggle_options_input)
        
        h_row1.addWidget(self.new_q_input)
        h_row1.addWidget(self.q_type_combo)
        c_layout.addLayout(h_row1)
        
        self.options_input = QLineEdit()
        self.options_input.setPlaceholderText("Options comma separated (e.g. Happy, Sad, Neutral)")
        self.options_input.setVisible(False)
        c_layout.addWidget(self.options_input)

        self.add_q_btn = QPushButton("Add to Schema")
        self.add_q_btn.clicked.connect(self.add_question)
        c_layout.addWidget(self.add_q_btn)
        
        config_frame.setLayout(c_layout)
        self.main_layout.addWidget(config_frame)

        self.main_layout.addWidget(QLabel("<b>Data to Label:</b>"))
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.data_fields_layout = QVBoxLayout()
        self.scroll_content_widget.setLayout(self.data_fields_layout)
        self.scroll_area.setWidget(self.scroll_content_widget)
        
        self.main_layout.addWidget(self.scroll_area, stretch=1)

        self.main_layout.addWidget(QLabel("<b>Your Inputs:</b>"))
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout()
        self.form_widget.setLayout(self.form_layout)
        self.main_layout.addWidget(self.form_widget)

        action_layout = QHBoxLayout()
        self.progress_label = QLabel("Progress: 0/0")
        self.save_btn = QPushButton("Next")
        self.save_btn.clicked.connect(self.save_current)
        self.save_btn.setEnabled(False)
        
        action_layout.addWidget(self.progress_label)
        action_layout.addStretch()
        action_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(action_layout)

        self.setLayout(self.main_layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_next()

    def toggle_options_input(self):
        is_categorical = self.q_type_combo.currentText() == "Categorical (Multi-Options)"
        self.options_input.setVisible(is_categorical)

    def add_question(self):
        text = self.new_q_input.text().strip()
        q_type_sel = self.q_type_combo.currentText()
        
        if not text:
            QMessageBox.warning(self, "Error", "Question text is required.")
            return

        q_type_db = "boolean"
        options_db = ""

        if "Categorical" in q_type_sel:
            q_type_db = "categorical"
            options_db = self.options_input.text().strip()
            if not options_db:
                QMessageBox.warning(self, "Error", "Please provide comma-separated options for Categorical type.")
                return

        self.service.add_question(text, q_type_db, options_db)
        
        self.new_q_input.clear()
        self.options_input.clear()
        self.q_type_combo.setCurrentIndex(0)
        self.options_input.setVisible(False)
        
        self.load_next()
        QMessageBox.information(self, "Success", "Question added! Start labeling.")

    def refresh_form(self):
        """Rebuild the form based on current questions"""
        for i in reversed(range(self.form_layout.count())): 
            widget = self.form_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.dynamic_widgets = {}

        questions = self.service.get_questions()
        if not questions:
            self.form_layout.addWidget(QLabel("<i>No questions defined. Add one above.</i>"))
            return

        for q in questions:
            q_id = q['id']
            lbl = QLabel(q['text'])
            
            container_layout = QVBoxLayout()
            container_layout.addWidget(lbl)
            
            widget_ref = None

            if q['type'] == 'categorical':
                combo = QComboBox()
                opts = [o.strip() for o in q['options'].split(',')]
                combo.addItems(opts)
                container_layout.addWidget(combo)
                widget_ref = combo
            else:
                bg = QButtonGroup(self)
                rb_yes = QRadioButton("Yes")
                rb_no = QRadioButton("No")
                bg.addButton(rb_yes, 1)
                bg.addButton(rb_no, 0)
                
                h = QHBoxLayout()
                h.addWidget(rb_yes)
                h.addWidget(rb_no)
                h.addStretch()
                
                radio_container = QWidget()
                radio_container.setLayout(h)
                container_layout.addWidget(radio_container)
                widget_ref = bg
            
            wrapper = QWidget()
            wrapper.setLayout(container_layout)
            self.form_layout.addWidget(wrapper)
            
            self.dynamic_widgets[q_id] = {'widget': widget_ref, 'type': q['type']}

    def clear_data_fields(self):
        for i in reversed(range(self.data_fields_layout.count())):
            w = self.data_fields_layout.itemAt(i).widget()
            if w: w.setParent(None)

    def load_next(self):
        self.refresh_form()
        labeled, total = self.service.get_stats()
        self.progress_label.setText(f"Progress: {labeled}/{total}")
        
        self.clear_data_fields()
        
        data = self.service.get_next_unlabeled()
        if data:
            self.current_data = data
            
            questions = self.service.get_questions()
            self.save_btn.setEnabled(len(questions) > 0)
            
            meta = data['metadata']
            if not meta: 
                meta = {"Content": data['content']}

            for key, value in meta.items():
                label = QLabel(f"<b>{key}:</b>")
                
                text_box = AdjustableTextEdit(value)
                
                self.data_fields_layout.addWidget(label)
                self.data_fields_layout.addWidget(text_box)
                
            self.data_fields_layout.addStretch()
        else:
            self.current_data = None
            lbl = QLabel("✓ All data has been labeled!")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.data_fields_layout.addWidget(lbl)
            self.save_btn.setEnabled(False)

    def save_current(self):
        if not self.current_data: 
            return
        
        if not self.dynamic_widgets:
            QMessageBox.warning(self, "No Questions", "Please add at least one question to the schema first.")
            return
        
        answers = {}
        for q_id, info in self.dynamic_widgets.items():
            widget = info['widget']
            w_type = info['type']
            
            val = None
            if w_type == 'categorical':
                val = widget.currentText()
            else:
                if widget.checkedId() == -1:
                    QMessageBox.warning(self, "Incomplete", "Please answer all Yes/No questions.")
                    return
                val = "Yes" if widget.checkedId() == 1 else "No"
                
            answers[q_id] = val

        self.service.save_annotation(self.current_data['id'], answers)
        self.load_next()