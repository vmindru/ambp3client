DECODER_TYPE = {
    b'10': "AMBrc",
    b'11': "AMBMX",
    b'12': "TranX",
    b'13': "TranX Pro",
    b'14': "TranX Pro",
}

ERROR_CODES = {
   b'0001': 'CRC Error',
   b'0002': 'SOR Missing',
   b'0003': 'Header corrupt',
   b'0004': 'TOR Unknown',
   b'0005': 'Parameters missing',
   b'0006': 'Length of record to long',
   }

VERSION = {
    b'01': 'DECODER_TYPE',
    b'02': 'DESCRIPTION',
    b'03': 'VERSION',
    b'04': 'RELEASE',
    b'08': 'REGISTRATION',
    b'0A': 'BUILD_NUMBER',
    b'0C': 'OPTIONS',
    'DECODER_TYPE': DECODER_TYPE
}

PASSING = {
   b'01': 'PASSING_NUMBER',
   b'03': 'TRANSPONDER',
   b'04': 'RTC_TIME',
   b'05': 'STRENGTH',
   b'06': 'HITS',
   b'08': 'FLAGS'
   }

GENERAL = {
    b'81': 'DECODER_ID',
    b'83': 'CONTROLLER_ID',
    b'85': 'REQUEST_ID'
    }


STATUS = {
    b'01': 'NOISE',
    b'06': 'GPS',
    b'07': 'TEMPERATURE',
    b'0a': 'SATINUSE',
    b'0b': 'LOOP_TRIGGERS',
    b'0c': 'INPUT_VOLTAGE'
    }

ERROR = {
    b'1': 'CODE',
    b'02': 'DESCRIPTION',
    'ERROR_CODES': ERROR_CODES
}

RESEND = {}
RESET = {}
CLEAR_PASSING = {}
SERVER_SETTINGS = {}
SESSION = {}
NETWORK_SETTINGS = {}
WATCHDOG = {}
PING = {}
GET_TIME = {}
GENERAL_SETTINGS = {}
GPS_INFO = {}
FIRST_CONTACT = {}
SIGNALS = {}
LOOP_TRIGER = {}
TIMELINE = {}


type_of_records = {b'0000': {'tor_name': 'RESET', 'tor_fields': RESET},
                   b'0001': {'tor_name': 'PASSING', 'tor_fields': PASSING},
                   b'0002': {'tor_name': 'STATUS', 'tor_fields': STATUS},
                   b'0003': {'tor_name': 'VERSION', 'tor_fields': VERSION},
                   b'0004': {'tor_name': 'RESEND', 'tor_fields': RESEND},
                   b'0005': {'tor_name': 'CLEAR_PASSING', 'tor_fields': CLEAR_PASSING},
                   b'0013': {'tor_name': 'SERVER_SETTINGS', 'tor_fields': SERVER_SETTINGS},
                   b'0015': {'tor_name': 'SESSION', 'tor_fields': SESSION},
                   b'0016': {'tor_name': 'NETWORK_SETTINGS', 'tor_fields': NETWORK_SETTINGS},
                   b'0018': {'tor_name': 'WATCHDOG', 'tor_fields': WATCHDOG},
                   b'0020': {'tor_name': 'PING', 'tor_fields': PING},
                   b'0024': {'tor_name': 'GET_TIME', 'tor_fields': GET_TIME},
                   b'0028': {'tor_name': 'GENERAL_SETTINGS', 'tor_fields': GENERAL_SETTINGS},
                   b'0030': {'tor_name': 'GPS_INFO', 'tor_fields': GPS_INFO},
                   b'0045': {'tor_name': 'FIRST_CONTACT', 'tor_fields': FIRST_CONTACT},
                   b'002d': {'tor_name': 'SIGNALS', 'tor_fields': SIGNALS},
                   b'002f': {'tor_name': 'LOOP_TRIGGER', 'tor_fields': LOOP_TRIGER},
                   b'004a': {'tor_name': 'TIMELINE', 'tor_fields': TIMELINE},
                   b'FFFF': {'tor_name': 'ERROR', 'tor_fields': ERROR}
                   }


# NEED TO IMPLEMENT
# =====================================
#
# TOR (Type of Record) "RESEND" = 0x04
#
# =====================================
#
# Details (Fields of Record "RESEND"):
# FROM = 0x01 (4 byte)
# UNTIL = 0x02 (4 byte)
#
# General details (Fields of Record):
# DECODER_ID = 0x81 (4 byte)
# CONTROLLER_ID = 0x83 (4 byte)
# REQUEST_ID = 0x85 (8 byte)
# =====================================


# =====================================
#
# TOR (Type of Record) "CLEAR_PASSING" = 0x05
#
# =====================================
#
# Command
# [SOR(0x8e), DEFAULT_VERSION(0x02), 0x00, 0x00, 0x00(CRC), 0x00(CRC), 0x00, 0x00, TOR(0x05), 0x00, EOR(0x8f)]
#
# =====================================
#
# Returned record
# General details (Fields of Record):
# DECODER_ID = 0x81 (4 byte)
# CONTROLLER_ID = 0x83 (4 byte)
# REQUEST_ID = 0x85 (8 byte)
# =====================================
