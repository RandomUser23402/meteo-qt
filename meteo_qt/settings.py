import logging
import os

from PyQt5.QtCore import (QCoreApplication, QLocale, QSettings, QSize, Qt,
                          pyqtSignal)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDialog,
                             QDialogButtonBox, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QSpinBox,
                             QVBoxLayout)

try:
    import citylistdlg
    import proxydlg
except ImportError:
    from meteo_qt import citylistdlg
    from meteo_qt import proxydlg


class MeteoSettings(QDialog):
    applied_signal = pyqtSignal()

    def __init__(self, accurate_url, appid, parent=None):
        super(MeteoSettings, self).__init__(parent)
        self.settings = QSettings()
        trans_cities_dict = self.settings.value('CitiesTranslation') or '{}'
        self.trans_cities_dict = eval(trans_cities_dict)
        self.layout = QVBoxLayout()
        self.accurate_url = accurate_url
        self.appid = appid
        self.set_city = self.settings.value('City') or '?'
        locale = QLocale.system().name()
        locale_long = ['pt_BR', 'zh_CN', 'zh_TW']
        if locale not in locale_long:
            locale = locale[:2]
        self.interval_set = self.settings.value('Interval') or '30'
        self.temp_tray_color = self.settings.value('TrayColor') or ''
        # -----Cities comboBox------------------------
        self.first = True
        self.clear_combo = False
        self.city_list_before = []
        self.citylist = []
        self.city_combo = QComboBox()
        if self.set_city != '?':
            self.add_cities_incombo()
        self.city_combo.currentIndexChanged.connect(self.city_default)
        self.city_title = QLabel(self.tr('City'))
        self.city_button = QPushButton()
        self.city_button.setIcon(QIcon.fromTheme("configure", QIcon(':/configure')))
        self.city_button.setToolTip(self.tr('Click to edit the cities list'))
        self.city_button.clicked.connect(self.edit_cities_list)
        # ------Language------------------------------
        self.language_label = QLabel(self.tr('Language'))
        self.language_combo = QComboBox()
        self.language_combo.setToolTip(
            QCoreApplication.translate(
                'Tooltip',
                'The application has to be restared to apply the language setting',
                'Settings dialogue'
            )
        )
        self.language_dico = {'bg': self.tr('Bulgarian'),
                              'ca': self.tr('Catalan'),
                              'cs': self.tr('Czech'),
                              'da': self.tr('Danish'),
                              'de': self.tr('German'),
                              'el': self.tr('Greek'),
                              'en': self.tr('English'),
                              'es': self.tr('Spanish'),
                              'fi': self.tr('Finnish'),
                              'fr': self.tr('French'),
                              'he': self.tr('Hebrew'),
                              'hr': self.tr('Croatian'),
                              'hu': self.tr('Hungarian'),
                              'it': self.tr('Italian'),
                              'ja': self.tr('Japanese'),
                              'lt': self.tr('Lithuanian'),
                              'nb': self.tr('Norwegian (Bokmaal)'),
                              'nl': self.tr('Dutch'),
                              'pl': self.tr('Polish'),
                              'pt': self.tr('Portuguese'),
                              'pt_BR': self.tr('Brazil Portuguese'),
                              'ro': self.tr('Romanian'),
                              'ru': self.tr('Russian'),
                              'sk': self.tr('Slovak'),
                              'sv': self.tr('Swedish'),
                              'tr': self.tr('Turkish'),
                              'uk': self.tr('Ukrainian'),
                              'zh_TW': self.tr('Chinese Traditional'),
                              'zh_CN': self.tr('Chinese Simplified')}
        lang_list = sorted(self.language_dico.values())
        # English as fallback language
        if locale not in self.language_dico:
            locale = 'en'
        self.setLanguage = self.settings.value('Language') or locale
        self.language_combo.addItems(lang_list)
        self.language_combo.setCurrentIndex(
            self.language_combo.findText(self.language_dico[self.setLanguage])
        )
        self.language_combo.currentIndexChanged.connect(self.language)
        self.lang_changed = False
        # Unit system
        self.units_changed = False
        self.temp_unit = self.settings.value('Unit')
        if self.temp_unit is None or self.temp_unit == '':
            self.temp_unit = 'metric'
            self.units_changed = True
        self.units_label = QLabel(self.tr('Temperature unit'))
        self.units_combo = QComboBox()
        self.units_dico = {'metric': '°C', 'imperial': '°F', ' ': '°K'}
        units_list = sorted(self.units_dico.values())
        self.units_combo.addItems(units_list)
        self.units_combo.setCurrentIndex(self.units_combo.findText(
            self.units_dico[self.temp_unit]))
        self.units_combo.currentIndexChanged.connect(self.units)
        # Beaufort
        self.bft_checkbox = QCheckBox(
            QCoreApplication.translate(
                'Wind unit - Checkbox label',
                'Wind unit in Beaufort',
                'Settings dialogue'
            )
        )
        bft_bool = self.settings.value('Beaufort') or 'False'
        self.bft_bool = eval(bft_bool)
        self.bft_checkbox.setChecked(self.bft_bool)
        self.bft_checkbox.stateChanged.connect(self.beaufort)
        self.bft_changed = False
        # Decimal in trayicon
        self.temp_decimal_label = QLabel(
            QCoreApplication.translate(
                'If the temperature will be shown with a decimal or rounded in tray icon',
                'Temperature accuracy in system tray', 'Settings dialogue'
            )
        )
        self.temp_decimal_combo = QComboBox()
        temp_decimal_combo_dico = {'False': '0°', 'True': '0.1°'}
        temp_decimal_combo_list = [
            temp_decimal_combo_dico['False'], temp_decimal_combo_dico['True']
        ]
        self.temp_decimal_combo.addItems(temp_decimal_combo_list)
        temp_decimal_bool_str = self.settings.value('Decimal') or 'False'
        self.temp_decimal_combo.setCurrentIndex(
            self.temp_decimal_combo.findText(
                temp_decimal_combo_dico[temp_decimal_bool_str]
            )
        )
        self.temp_decimal_combo.currentIndexChanged.connect(self.temp_decimal)
        self.temp_decimal_changed = False
        # Interval of updates
        self.interval_label = QLabel(self.tr('Update interval'))
        self.interval_min = QLabel(self.tr('minutes'))
        self.interval_combo = QComboBox()
        self.interval_list = ['15', '30', '45', '60', '90', '120']
        self.interval_combo.addItems(self.interval_list)
        self.interval_combo.setCurrentIndex(self.interval_combo.findText(
            self.interval_list[self.interval_list.index(self.interval_set)]))
        self.interval_combo.currentIndexChanged.connect(self.interval)
        self.interval_changed = False
        # OK Cancel Apply Buttons
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addStretch()
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )
        self.buttonBox.setContentsMargins(0, 30, 0, 0)
        self.buttonLayout.addWidget(self.buttonBox)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
        # Autostart
        self.autostart_label = QLabel(self.tr('Launch at startup'))
        self.autostart_checkbox = QCheckBox()
        autostart_bool = self.settings.value('Autostart') or 'False'
        autostart_bool = eval(autostart_bool)
        self.autostart_checkbox.setChecked(autostart_bool)
        self.autostart_checkbox.stateChanged.connect(self.autostart)
        self.autostart_changed = False
        # Tray temp° color
        self.temp_colorLabel = QLabel(self.tr('Font colour in the tray'))
        self.temp_colorButton = QPushButton()
        self.temp_colorButton.setStyleSheet(
            'QWidget {{ background-color: {0} }}'.format(self.temp_tray_color))
        self.temp_colorButton.setMaximumSize(QSize(44, 24))
        self.temp_colorButton.clicked.connect(self.color_chooser)
        self.temp_color_resetButton = QPushButton(self.tr('Reset'))
        self.temp_color_resetButton.setToolTip(
            self.tr('Reset font colour to system default'))
        self.temp_color_resetButton.clicked.connect(self.color_reset)
        # Display notifications
        self.notifier_label = QLabel(self.tr('Notification on weather update'))
        self.notifier_checkbox = QCheckBox()
        notifier_bool = self.settings.value('Notifications') or 'True'
        notifier_bool = eval(notifier_bool)
        self.notifier_checkbox.setChecked(notifier_bool)
        self.notifier_checkbox.stateChanged.connect(self.notifier)
        self.notifier_changed = False
        # Icon & Temp
        self.tray_icon_temp_label = QLabel(QCoreApplication.translate(
            "Settings dialogue", "System tray icon",
            '''Setting to choose the type of the icon on the tray (only icon,
            only text, icon&text'''))
        self.tray_icon_combo = QComboBox()
        tray_icon_temp = QCoreApplication.translate(
            "Settings dialogue", "Icon & temperature",
            'Setting to choose the type of the icon on the tray')
        tray_icon = QCoreApplication.translate(
            "Settings dialogue", "Icon",
            'Setting to choose the type of the icon on the tray')
        tray_temp = QCoreApplication.translate(
            "Settings dialogue", "Temperature",
            'Setting to choose the type of the icon on the tray')
        self.tray_dico = {'icon&temp': tray_icon_temp, 'icon': tray_icon,
                          'temp': tray_temp}
        set_tray_icon = self.settings.value('TrayType') or 'icon&temp'
        tray_icon_list = sorted(self.tray_dico.values())
        self.tray_icon_combo.addItems(tray_icon_list)
        self.tray_icon_combo.setCurrentIndex(self.tray_icon_combo.findText
                                             (self.tray_dico[set_tray_icon]))
        self.tray_icon_combo.currentIndexChanged.connect(self.tray)
        self.tray_changed = False
        # New (flat) or old (shaded) icon type
        self.shaded_weather_icons_label = QLabel(self.tr('Use shaded weather icons'))
        self.shaded_weather_icons_checkbox = QCheckBox()
        shaded_weather_icons_bool = self.settings.value('ShadedIcons') or 'True'
        shaded_weather_icons_bool = eval(shaded_weather_icons_bool)
        self.shaded_weather_icons_checkbox.setChecked(shaded_weather_icons_bool)
        self.shaded_weather_icons_checkbox.stateChanged.connect(self.shaded_weather_icons)
        self.shaded_weather_icons_changed = False
        # Font size
        fontsize = self.settings.value('FontSize') or '18'
        self.fontsize_label = QLabel(QCoreApplication.translate(
            "Settings dialog", "Font size in tray",
            "Setting for the font size of the temperature in the tray icon"))
        self.fontsize_spinbox = QSpinBox()
        self.fontsize_spinbox.setRange(12, 32)
        self.fontsize_spinbox.setValue(int(fontsize))
        if fontsize is None or fontsize == '':
            self.settings.setValue('FontSize', '18')
        self.fontsize_changed = False
        self.fontsize_spinbox.valueChanged.connect(self.fontsize_change)
        # Font weight
        self.bold_checkbox = QCheckBox(
            QCoreApplication.translate(
                'Font setting - Checkbox label',
                'Bold',
                'Settings dialogue'
            )
        )
        bold_bool = self.settings.value('Bold') or 'False'
        self.bold_bool = eval(bold_bool)
        self.bold_checkbox.setChecked(self.bold_bool)
        self.bold_checkbox.stateChanged.connect(self.bold)
        self.bold_changed = False
        # Proxy
        self.proxy_label = QLabel(
            QCoreApplication.translate(
                'Checkbox',
                'Connection by proxy',
                'Settings dialogue'
            )
        )
        self.proxy_chbox = QCheckBox()
        proxy_bool = self.settings.value('Proxy') or 'False'
        self.proxy_bool = eval(proxy_bool)
        self.proxy_chbox.setChecked(self.proxy_bool)
        self.proxy_chbox.stateChanged.connect(self.proxy)
        self.proxy_changed = False
        self.proxy_button = QPushButton(
            QCoreApplication.translate(
                'Label of button to open the proxy dialogue',
                'Settings',
                'Settings dialogue'
            )
        )
        self.proxy_button.clicked.connect(self.proxy_settings)
        self.proxy_button.setEnabled(self.proxy_bool)
        # Openweathermap key
        self.owmkey_label = QLabel(
            QCoreApplication.translate(
                'The key that user can generate in his OpenWeatherMap profile',
                'OpenWeatherMap key',
                'Settings dialogue'
            )
        )
        self.owmkey_create = QLabel(
            QCoreApplication.translate(
                'Link to create a profile in OpenWeatherMap',
                "<a href=\"http://home.openweathermap.org/users/sign_up\">Create key</a>",
                'Settings dialogue'
            )
        )
        self.owmkey_create.setOpenExternalLinks(True)
        apikey = self.settings.value('APPID') or ''
        self.owmkey_text = QLineEdit()
        self.owmkey_text.setText(apikey)
        self.owmkey_text.textChanged.connect(self.apikey_changed)

        self.start_minimized_label = QLabel(
            QCoreApplication.translate(
                'Checkable option to show or not the window at startup',
                'Start minimized',
                'Settings dialogue'
            )
        )
        self.start_minimized_chbx = QCheckBox()
        start_minimized_bool = self.settings.value('StartMinimized') or 'True'
        self.start_minimized_bool = eval(start_minimized_bool)
        self.start_minimized_chbx.setChecked(self.start_minimized_bool)
        self.start_minimized_chbx.stateChanged.connect(self.start_minimized)
        self.start_minimized_changed = False

        # ----------
        self.panel = QGridLayout()
        self.panel.addWidget(self.city_title, 0, 0)
        self.panel.addWidget(self.city_combo, 0, 1)
        self.panel.addWidget(self.city_button, 0, 2)
        self.panel.addWidget(self.language_label, 1, 0)
        self.panel.addWidget(self.language_combo, 1, 1)
        self.panel.addWidget(self.units_label, 2, 0)
        self.panel.addWidget(self.units_combo, 2, 1)
        self.panel.addWidget(self.bft_checkbox, 2, 2)
        self.panel.addWidget(self.temp_decimal_label, 3, 0)
        self.panel.addWidget(self.temp_decimal_combo, 3, 1)
        self.panel.addWidget(self.interval_label, 4, 0)
        self.panel.addWidget(self.interval_combo, 4, 1)
        self.panel.addWidget(self.interval_min, 4, 2)
        self.panel.addWidget(self.autostart_label, 5, 0)
        self.panel.addWidget(self.autostart_checkbox, 5, 1)
        self.panel.addWidget(self.temp_colorLabel, 6, 0)
        self.panel.addWidget(self.temp_colorButton, 6, 1)
        self.panel.addWidget(self.temp_color_resetButton, 6, 2)
        self.panel.addWidget(self.notifier_label, 7, 0)
        self.panel.addWidget(self.notifier_checkbox, 7, 1)
        self.panel.addWidget(self.tray_icon_temp_label, 8, 0)
        self.panel.addWidget(self.tray_icon_combo, 8, 1)
        self.panel.addWidget(self.shaded_weather_icons_label, 9, 0)
        self.panel.addWidget(self.shaded_weather_icons_checkbox, 9, 1)
        self.panel.addWidget(self.fontsize_label, 10, 0)
        self.panel.addWidget(self.fontsize_spinbox, 10, 1)
        self.panel.addWidget(self.bold_checkbox, 10, 2)
        self.panel.addWidget(self.proxy_label, 11, 0)
        self.panel.addWidget(self.proxy_chbox, 11, 1)
        self.panel.addWidget(self.proxy_button, 11, 2)
        self.panel.addWidget(self.owmkey_label, 12, 0)
        self.panel.addWidget(self.owmkey_text, 12, 1)
        self.panel.addWidget(self.owmkey_create, 12, 2)
        self.panel.addWidget(self.start_minimized_label, 13, 0)
        self.panel.addWidget(self.start_minimized_chbx, 13, 1)

        self.layout.addLayout(self.panel)
        self.layout.addLayout(self.buttonLayout)
        self.statusbar = QLabel()
        self.layout.addWidget(self.statusbar)
        self.nokey_message = QCoreApplication.translate(
            'Warning message after pressing Ok',
            'Please enter your OpenWeatherMap key',
            'Settings dialogue'
        )
        self.nocity_message = QCoreApplication.translate(
            'Warning message after pressing OK',
            'Please add a city',
            'Settings dialogue'
        )
        self.setLayout(self.layout)
        self.setWindowTitle(self.tr('Meteo-qt Configuration'))

    def units(self):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        self.units_changed = True

    def language(self):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        self.lang_changed = True

    def city_default(self):
        allitems = [
            self.city_combo.itemText(i) for i in range(self.city_combo.count())
        ]
        allitems_not_translated = []
        for i in allitems:
            allitems_not_translated.append(self.find_city_key(i))
        city_name = self.city_combo.currentText()
        city_name = self.find_city_key(city_name)
        citytosave = city_name.split('_')
        # This self variable will serve to check if a translation
        # exist for the current city when quitting
        self.citytosave = '_'.join(citytosave)
        if len(citytosave) < 3:
            return
        self.id_before = citytosave[2]
        self.city_before = citytosave[0]
        self.country_before = citytosave[1]
        self.city_list_before = allitems_not_translated[:]
        self.city_list_before.pop(self.city_list_before.index(city_name))
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def interval(self):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        self.interval_changed = True

    def edit_cities_list(self):
        apikey = self.owmkey_text.text()
        apiid = '&APPID=' + apikey
        if apikey == '':
            self.statusbar.setText(self.nokey_message)
            return
        dialog = citylistdlg.CityListDlg(
            self.citylist, self.accurate_url, apiid,
            self.trans_cities_dict, self
        )
        dialog.citieslist_signal.connect(self.cities_list)
        dialog.citiesdict_signal.connect(self.cities_dict)
        dialog.exec_()

    def cities_dict(self, cit_dict):
        self.trans_cities_dict = cit_dict

    def cities_list(self, cit_list):
        if len(cit_list) > 0:
            citytosave = cit_list[0].split('_')
            self.id_before = citytosave[2]
            self.city_before = citytosave[0]
            self.country_before = citytosave[1]
            if len(cit_list) > 1:
                self.city_list_before = cit_list[1:]
            else:
                self.city_list_before = str('')
        else:
            self.id_before = ''
            self.city_before = ''
            self.country_before = ''
            self.city_list_before = []
            self.clear_combo = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        self.first = False
        self.add_cities_incombo()

    def autostart(self, state):
        self.autostart_state = state
        self.autostart_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def autostart_apply(self):
        dir_auto = '/.config/autostart/'
        d_file = 'meteo-qt.desktop'
        home = os.getenv('HOME')
        total_path = home + dir_auto + d_file
        if self.autostart_state == 2:
            desktop_file = ['[Desktop Entry]\n',
                            'Exec=meteo-qt\n',
                            'Name=meteo-qt\n',
                            'Type=Application\n',
                            'Version=1.0\n',
                            'X-LXQt-Need-Tray=true\n']
            if not os.path.exists(home + dir_auto):
                os.system('mkdir -p {}'.format(os.path.dirname(total_path)))
            with open(total_path, 'w') as out_file:
                out_file.writelines(desktop_file)
            self.settings.setValue('Autostart', 'True')
            logging.debug('Write desktop file in ~/.config/autostart')
        elif self.autostart_state == 0:
            if os.path.exists(total_path):
                os.remove(total_path)
            self.settings.setValue('Autostart', 'False')
            logging.debug('Remove desktop file from ~/.config/autostart')
        else:
            return

    def color_chooser(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.temp_colorButton.setStyleSheet(
                'QWidget {{ background-color: {0} }}'.format(col.name()))
            # focus to next elem to show immediatley the colour
            # in the button (in some DEs)
            self.temp_color_resetButton.setFocus()
            self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
            self.color_before = col.name()
        else:
            logging.debug('Invalid color:' + str(col))

    def color_reset(self):
        self.temp_colorButton.setStyleSheet('QWidget { background-color:  }')
        self.color_before = ''
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def notifier(self, state):
        self.notifier_state = state
        self.notifier_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def notifier_apply(self):
        if self.notifier_state == 2:
            self.settings.setValue('Notifications', 'True')
            logging.debug('Write: Notifications = True')
        elif self.notifier_state == 0:
            self.settings.setValue('Notifications', 'False')
            logging.debug('Write: Notifications = False')

    def temp_decimal(self, state):
        self.temp_decimal_state = state
        self.temp_decimal_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def tray(self):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        self.tray_changed = True

    def tray_apply(self):
        tray = self.tray_icon_combo.currentText()
        self.settings.setValue('Tray', tray)
        logging.debug('Write >' + 'Tray >' + str(tray))
        settray = [
            key for key, value in self.tray_dico.items() if value == tray
        ]
        self.settings.setValue('TrayType', settray[0])
    
    def shaded_weather_icons(self, state):
        self.shaded_weather_icons_state = state
        self.shaded_weather_icons_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def shaded_weather_icons_apply(self):
        if self.shaded_weather_icons_state == 2:
            shaded_icons = 'True'
        else:
            shaded_icons = 'False'
        self.settings.setValue('ShadedIcons', str(shaded_icons))

    def fontsize_change(self, size):
        self.fontsize_changed = True
        self.fontsize_value = size
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def fontsize_apply(self):
        logging.debug('Apply fontsize: ' + str(self.fontsize_value))
        self.settings.setValue('FontSize', str(self.fontsize_value))

    def bold(self, state):
        self.bold_state = state
        self.bold_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def bold_apply(self):
        if self.bold_state == 2:
            bold = 'True'
        else:
            bold = 'False'
        self.settings.setValue('Bold', str(bold))

    def start_minimized(self, state):
        self.start_minimized_state = state
        self.start_minimized_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def start_minimized_apply(self):
        if self.start_minimized_state == 2:
            start_minimized = 'True'
        else:
            start_minimized = 'False'
        self.settings.setValue('StartMinimized', start_minimized)

    def beaufort(self, state):
        self.bft_state = state
        self.bft_changed = True
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def beaufort_apply(self):
        if self.bft_state == 2:
            bft = 'True'
        else:
            bft = 'False'
        self.settings.setValue('Beaufort', str(bft))

    def proxy(self, state):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
        if state == 2:
            self.proxy_bool = True
            self.proxy_button.setEnabled(True)
        else:
            self.proxy_bool = False
            self.proxy_button.setEnabled(False)

    def proxy_settings(self):
        dialog = proxydlg.Proxy(self)
        dialog.exec_()

    def apikey_changed(self):
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)

    def apply_settings(self):
        self.accepted()

    def clear_translations(self):
        ''' Save the list of the current cities list
            and remove the odd or blank translations'''
        self.settings.setValue('CityList', str(self.citylist))
        translations_to_delete = []
        for key, value in self.trans_cities_dict.items():
            if key == value or value == '' or key not in self.citylist:
                translations_to_delete.append(key)
        for i in translations_to_delete:
            del self.trans_cities_dict[i]
        self.settings.setValue(
            'CitiesTranslation', str(self.trans_cities_dict)
        )
        logging.debug(
            'write ' + 'CitiesTranslation ' + str(self.trans_cities_dict)
        )

    def accepted(self):
        self.clear_translations()
        apikey = self.owmkey_text.text()
        city_name = self.city_combo.currentText()
        if apikey == '':
            self.statusbar.setText(self.nokey_message)
            return
        else:
            self.statusbar.setText('')
            self.settings.setValue('APPID', str(self.owmkey_text.text()))
        if city_name == '':
            self.statusbar.setText(self.nocity_message)
            return
        else:
            self.statusbar.setText('')
        self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
        if hasattr(self, 'id_before'):
            self.settings.setValue('ID', self.id_before)
            logging.debug('write ' + 'ID' + str(self.id_before))
        if hasattr(self, 'city_before'):
            self.settings.setValue('City', self.city_before)
            logging.debug('write ' + 'City' + str(self.city_before))
        if hasattr(self, 'country_before'):
            self.settings.setValue('Country', self.country_before)
            logging.debug('write ' + 'Country' + str(self.country_before))
        if hasattr(self, 'color_before'):
            self.settings.setValue('TrayColor', self.color_before)
            if self.color_before == '':
                self.color_before = 'None'
            logging.debug(
                'Write font color for temp in tray: {0}'.format(self.color_before)
            )
        if self.autostart_changed:
            self.autostart_apply()
        if self.interval_changed:
            time = self.interval_combo.currentText()
            self.settings.setValue('Interval', time)
            logging.debug('Write ' + 'Interval ' + str(time))
        if self.lang_changed:
            lang = self.language_combo.currentText()
            setlang = [
                key for key, value in self.language_dico.items() if value == lang
            ]
            self.settings.setValue('Language', setlang[0])
            logging.debug('Write ' + 'Language ' + str(setlang[0]))
        if self.units_changed:
            unit = self.units_combo.currentText()
            setUnit = [
                key for key, value in self.units_dico.items() if value == unit
            ]
            self.settings.setValue('Unit', setUnit[0])
            logging.debug('Write ' + 'Unit ' + str(setUnit[0]))
        if self.temp_decimal_changed:
            decimal = self.temp_decimal_combo.currentText()
            decimal_bool_str = 'False'
            if decimal == '0.1°':
                decimal_bool_str = 'True'
            self.settings.setValue('Decimal', decimal_bool_str)
            logging.debug('Write: Decimal in tray icon = ' + decimal_bool_str)
        if self.notifier_changed:
            self.notifier_apply()
        if self.tray_changed:
            self.tray_apply()
        if self.shaded_weather_icons_changed:
            self.shaded_weather_icons_apply()
        if self.fontsize_changed:
            self.fontsize_apply()
        if self.bold_changed:
            self.bold_apply()
        if self.bft_changed:
            self.beaufort_apply()
        if self.start_minimized_changed:
            self.start_minimized_apply()
        proxy_url = self.settings.value('Proxy_url') or ''
        if proxy_url == '':
            self.proxy_bool = False
        self.settings.setValue('Proxy', str(self.proxy_bool))
        self.applied_signal.emit()

    def accept(self):
        self.accepted()
        apikey = self.owmkey_text.text()
        city_name = self.city_combo.currentText()
        if apikey == '':
            self.statusbar.setText(self.nokey_message)
            return
        if city_name == '':
            self.statusbar.setText(self.nocity_message)
            return
        QDialog.accept(self)

    def add_cities_incombo(self):
        list_cities = ''
        self.city_combo.clear()
        if self.clear_combo:
            return
        if self.first:
            list_cities = self.settings.value('CityList')
            if list_cities is not None:
                self.city_list_before = list_cities[:]
            self.citylist = [
                self.set_city + '_'
                + self.settings.value('Country') + '_'
                + self.settings.value('ID')
            ]
        else:
            self.citylist = [
                self.city_before + '_' + self.country_before
                + '_' + self.id_before
            ]
            list_cities = self.city_list_before[:]
        if list_cities is None:
            list_cities = []
        if list_cities != '' and list_cities is not None:
            if type(list_cities) is str:
                list_cities = eval(list_cities)
            self.citylist = self.citylist + list_cities
        duplicate = []
        for i in self.citylist:
            if i not in duplicate:
                duplicate.append(i)
        self.citylist = duplicate[:]
        self.translated = []
        for city in self.citylist:
            self.translated.append(self.trans_cities_dict.get(city, city))
        self.city_combo.addItems(self.translated)
        if len(list_cities) > 0:
            maxi = len(max(list_cities, key=len))
            self.city_combo.setMinimumSize(maxi * 8, 23)

    def find_city_key(self, city):
        for key, value in self.trans_cities_dict.items():
            if value == city:
                return key
        return city
