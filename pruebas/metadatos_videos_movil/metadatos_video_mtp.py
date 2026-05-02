'''

'''
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

def obtener_gps_video(ruta_archivo):
    parser = createParser(ruta_archivo)
    with parser:
        metadata = extractMetadata(parser)
        if metadata:
            return metadata
    return None

print(obtener_gps_video("C:\FotosTemp/VID_20250512_101613.mp4"))
