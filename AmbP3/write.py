from .decoder import bin_to_decimal


def dict_to_sqlquery(data_dict, table):
    columns_string = "( {} )".format(','.join(data_dict.keys()))
    values_string = "( {} )".format(','.join(['%s'] * len(data_dict.values())))
    sql = """INSERT INTO {} {} VALUES {}""".format(table, columns_string, values_string)
    return sql


class Write:
    def to_file(data, file_handler):
        if not file_handler.closed:
            try:
                file_handler.write(f'\n{data}')
                file_handler.flush()
            except IOError:
                print("Can not write to {}".format(file_handler.name))
        else:
            print("{} is not a filehandler".format(file_handler))

    def passing_to_mysql(cursor, result, table='passes'):
        result = result['RESULT']
        mysql_p3_map = {
            'pass_id': 'PASSING_NUMBER',
            'transponder_id': 'TRANSPONDER',
            'rtc_time': 'RTC_TIME',
            'strength': 'STRENGTH',
            'hits': 'HITS',
            'flags': 'FLAGS',
            'decoder_id': 'DECODER_ID'
        }
        mysql_insert = {}
        if 'TOR' in result and result['TOR'] == 'PASSING':
            for key, value in mysql_p3_map.items():
                if value in result:
                    my_key = key
                    my_value = bin_to_decimal(result[value])
                    mysql_insert[my_key] = my_value
        query = dict_to_sqlquery(mysql_insert, table)
        print("inserting: {}:".format(list(mysql_insert.values())))
        cursor.execute(query, list(mysql_insert.values()))
