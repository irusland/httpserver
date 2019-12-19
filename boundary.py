from email.message import Message

my_multipart_data = (b'Content-Type: multipart/form-data; '
                     b'boundary="===============1107021068307284864=="\n'
                     b'\n'
                     b'--===============1107021068307284864==\n'
                     b'Content-Type: text/plain\n'
                     b'MIME-Version: 1.0\n'
                     b'Content-Disposition: form-data; name="foo"\n'
                     b'\n'
                     b'bar\n'
                     b'--===============1107021068307284864==\n'
                     b'Content-Type: text/plain\n'
                     b'MIME-Version: 1.0\n'
                     b'Content-Disposition: form-data; name="name"\n'
                     b'\n'
                     b'jd\n'
                     b'--===============1107021068307284864==--')

mp = (
      b'Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryTnnCRhLhxTtf3f01\n'
      b'\n'
      b'------WebKitFormBoundaryTnnCRhLhxTtf3f01\n'
      b'Content-Disposition: form-data; name="file"; filename="n"\n'
      b'Content-Type: application/octet-stream\n'
      b'\n'
      b'\n'
      b'------WebKitFormBoundaryTnnCRhLhxTtf3f01\n'
      b'Content-Disposition: form-data; name="f"; filename="a"\n'
      b'Content-Type: application/octet-stream\n'
      b'Content: m\n'
      b'\n'
      b'asdasdasdasdasdasd\n'
      b'------WebKitFormBoundaryTnnCRhLhxTtf3f01--\n')


def main():
    import email.parser

    msg: Message = email.parser.BytesParser().parsebytes(mp)
    print(msg)

    print({
        part.get_param('name', header='content-disposition'):
            (part.get_payload(decode=True),
             part.get_param('filename', header='content-disposition'))
        for part in msg.get_payload()
    },
        [
            part.get_payload()
        for part in msg.get_payload()])


if __name__ == '__main__':
    main()
