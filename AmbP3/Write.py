class Write():
    def to_file(data, file_handler):
        if not file_handler.closed:
            try:
                file_handler.write(data)
                file_handler.flush()
            except IOError:
                print("Can not write to {}".format(file_handler.name))
        else:
            print("{} is not a filehandler".format(file_handler))
