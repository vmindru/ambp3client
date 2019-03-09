PASSING = {
   0x01: 'PASSING_NUMBER',
   0x03: 'TRANSPONDER',
   0x04: 'RTC_TIME',
   0x05: 'STRENGTH',
   0x06: 'HITS',
   0x08: 'FLAGS'
   }

STATUS = {
    0x01: 'NOISE',
    0x06: 'GPS',
    0x07: 'TEMPERATURE',
    0x0A: 'SATINUSE',
    0x0B: 'LOOP_TRIGGERS',
    0x0C: 'INPUT_VOLTAGE'
    }


type_of_records = {0x00: {'name': 'RESET', 'fields': {}},
                   0x01: {'name': 'PASSING', 'fields': PASSING},
                   0x02: {'name': 'STATUS', 'fields': STATUS},
                   0x45: {'name': 'FIRST_CONTACT', 'fields': {}},
                   0x03: {'name': 'VERSION', 'fields': {}},
                   0x04: {'name': 'RESEND', 'fields': {}},
                   0x05: {'name': 'CLEAR_PASSING', 'fields': {}},
                   0x18: {'name': 'WATCHDOG', 'fields': {}},
                   0x20: {'name': 'PING', 'fields': {}},
                   0x2d: {'name': 'SIGNALS', 'fields': {}},
                   0x13: {'name': 'SERVER_SETTINGS', 'fields': {}},
                   0x15: {'name': 'SESSION', 'fields': {}},
                   0x28: {'name': 'GENERAL_SETTINGS', 'fields': {}},
                   0x2f: {'name': 'LOOP_TRIGGER', 'fields': {}},
                   0x30: {'name': 'GPS_INFO', 'fields': {}},
                   0x4a: {'name': 'TIMELINE', 'fields': {}},
                   0x24: {'name': 'GET_TIME', 'fields': {}},
                   0x16: {'name': 'NETWORK_SETTINGS', 'fields': {}},
                   0xFFFF: {'name': 'ERROR', 'fields': {}}
                   }
