import earthaccess
import netCDF4 as nc
import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from skimage import exposure
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import reverse_geocoder as rg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import warnings
warnings.filterwarnings("ignore")





def download_data_EMIT(user, password, bx, date, short_nm):

    # Set User and Pass
    os.environ['EARTHDATA_USERNAME'] = user
    os.environ['EARTHDATA_PASSWORD'] = password

    auth = earthaccess.login()

    print('====================')
    print('Searching Image EMIT')
    print('====================')

    results = earthaccess.search_data(
        short_name=short_nm,            # 'EMITL2ARFL' 'EMITL2BMIN'
        cloud_hosted=True,
        bounding_box=bx,
        temporal=date,
        count=10
    )

    y, m, d = date[0].split('-')
    

    if len(results) == 0:
        while len(results) == 0 and int(y) != 2021: # EMIT dates: 2022 - ongoing

            if int(m) == 1:
                y = int(y) - 1
                m = 12
            else:
                m = int(m) - 1
            date = (str(y) + '-' + str(m) + '-' + d, date[1])
            print('Search Image Date: ',date[0])


            results = earthaccess.search_data(
                short_name='EMITL2ARFL',
                cloud_hosted=True,
                bounding_box=bx,
                temporal=date,
                count=10
            )
    
    a,b,c,d = bx
    folder = 'LAT'+str(a)+'_LON'+str(b)
    folder = folder.replace('.','')
    os.makedirs('./data/'+folder, exist_ok=True)
            
    # Downloading...
    url = (results[0]['umm']['RelatedUrls'][1]['URL'])
    name_file = url[url.rfind("/")+1:] if "/" in url else url
    print('=================================================================')
    print(f"EMIT Downloading: {name_file}")
    print('=================================================================')
    os.system(f'curl --user {user}:{password} -o ./data/{folder}/{name_file} -O -b ~/.urs_cookies -c ~/.urs_cookies -L -n {url}')

    return folder, name_file, date[0]




def analysis(path, save_path):

    print('\nProccesing...\n')

    refl = xr.open_dataset(path)

    wvl = xr.open_dataset(path,group='sensor_band_parameters')

    # This will utilize the wvl dataset dictionary as the ds coordinates dictionary
    ds = refl.assign_coords({'downtrack':(['downtrack'], refl.downtrack.data),'crosstrack':(['crosstrack'],refl.crosstrack.data), **wvl.variables})

    # ====================== RGB =========================
    print('RGB Image...')
    r = np.nanargmin(abs(ds['wavelengths'].values-620)) # 620
    g = np.nanargmin(abs(ds['wavelengths'].values-550)) # 590
    b = np.nanargmin(abs(ds['wavelengths'].values-450)) # 450

    r = ds.sel(bands=r)['reflectance'].values
    g = ds.sel(bands=g)['reflectance'].values
    b = ds.sel(bands=b)['reflectance'].values

    # Scale the matrices to the range of 0-255
    red_scaled = (r * 255 / np.max(r)).astype(np.uint8)
    green_scaled = (g * 255 / np.max(g)).astype(np.uint8)
    blue_scaled = (b * 255 / np.max(b)).astype(np.uint8)

    # Merge the matrices into a single 3-band matrix
    rgb = np.dstack((red_scaled, green_scaled, blue_scaled))

    # Contrast
    clip_limit = 0.02 
    rgb = exposure.equalize_adapthist(rgb, clip_limit=clip_limit)

    save = os.path.join(save_path, 'rgb.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(rgb)
    plt.axis('off')
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ================== NDVI ======================
    print('NDVI Image...')
    b650 = np.nanargmin(abs(ds['wavelengths'].values-650)) 
    b850 = np.nanargmin(abs(ds['wavelengths'].values-850)) 

    data650 = ds.sel(bands=b650)['reflectance'].values
    data850 = ds.sel(bands=b850)['reflectance'].values

    # Calculate
    ndvi = (data850 - data650) / (data850 + data650)
    ndvi = np.clip(ndvi, 0, np.inf)

    save = os.path.join(save_path, 'ndvi.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(ndvi, cmap=plt.cm.brg)
    plt.title('NDVI: Normalized Difference Vegetation Index')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ================== Iron Oxide Index ======================
    print('Iron Oxide Image...')
    r85 = np.nanargmin(abs(ds['wavelengths'].values-850)) 
    r65 = np.nanargmin(abs(ds['wavelengths'].values-650))

    r85 = ds.sel(bands=r85)['reflectance'].values
    r65 = ds.sel(bands=r65)['reflectance'].values

    # Calculate
    FeO = (r85 / r65)
    FeO = np.clip(FeO, 0, np.inf)

    save = os.path.join(save_path, 'iron_oxide.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(FeO, cmap='rainbow')
    plt.title('Iron Oxide Index')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ===================== AlOH ========================
    print('AlOH Image...')
    r22 = np.nanargmin(abs(ds['wavelengths'].values-2200))
    r17 = np.nanargmin(abs(ds['wavelengths'].values-1700))

    r22 = ds.sel(bands=r22)['reflectance'].values
    r17 = ds.sel(bands=r17)['reflectance'].values

    # Calculate
    AlOH = (r22 / r17)
    AlOH = np.clip(AlOH, 0, np.inf)

    save = os.path.join(save_path, 'alunite.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(AlOH, cmap='rainbow')
    plt.title('AlOH Index')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ===================== FEOOH =======================
    print('FEOOH Image...')
    r97 = np.nanargmin(abs(ds['wavelengths'].values-970))
    r90 = np.nanargmin(abs(ds['wavelengths'].values-900))

    r97 = ds.sel(bands=r97)['reflectance'].values
    r90 = ds.sel(bands=r90)['reflectance'].values

    # Calculate
    FeOOH = (r97 / r90)
    FeOOH = np.clip(FeOOH, 0, np.inf)

    save = os.path.join(save_path, 'FEOOH.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(FeOOH, cmap='rainbow')
    plt.title('Ferric Oxide-Oxyhydroxide Clay Index (FEOOH)')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ===================== AAI =======================
    print('AAI Image...')
    r22 = np.nanargmin(abs(ds['wavelengths'].values-2200))
    r21 = np.nanargmin(abs(ds['wavelengths'].values-2100))

    r22 = ds.sel(bands=r22)['reflectance'].values
    r21 = ds.sel(bands=r21)['reflectance'].values

    # Calculate
    AI = (r22 / r21)
    AI = np.clip(AI, 0, np.inf)

    save = os.path.join(save_path, 'AAI.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(AI, cmap='rainbow')
    plt.title('Argillic Alteration Index')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # ===================== AIS ======================
    print('AIS Image...')
    r22 = np.nanargmin(abs(ds['wavelengths'].values-2200)) 
    r23 = np.nanargmin(abs(ds['wavelengths'].values-2300))

    r22 = ds.sel(bands=r22)['reflectance'].values
    r23 = ds.sel(bands=r23)['reflectance'].values

    # Calculate
    AIS = (r22 / r23)
    AIS = np.clip(AIS, 0, np.inf)

    save = os.path.join(save_path, 'AIS.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(AIS, cmap='rainbow')
    plt.title('Argillic and Sericitic Alteration Index')
    plt.axis('off')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()

    # =================== DOS-2 ====================
    print('DOS-2 Image...')
    r79 = np.nanargmin(abs(ds['wavelengths'].values-790)) 
    r72 = np.nanargmin(abs(ds['wavelengths'].values-720)) 

    r79 = ds.sel(bands=r79)['reflectance'].values
    r72 = ds.sel(bands=r72)['reflectance'].values

    # Calculate
    DOS2 = (r79 - r72)/(r79 + r72)
    DOS2 = np.clip(DOS2, 0, np.inf)

    save = os.path.join(save_path, 'DOS.png')

    # Plot
    plt.subplots(figsize=(35,35))
    plt.imshow(DOS2, cmap='rainbow')
    plt.title('Red Edge Position 3')
    plt.axis('on')
    plt.colorbar(fraction=0.046, pad=0.01)
    plt.savefig(save, bbox_inches='tight')
    plt.close()





def region2(latitud, longitud):
    coordenadas = (latitud, longitud)
    resultados = rg.search(coordenadas)
    
    if resultados:
        lugar = resultados[0]
        return f"{lugar['name']} {lugar['admin1']} {lugar['cc']}"
    else:
        return "No se encontró información de ubicación para estas coordenadas."

def region(latitud, longitud):
    geolocalizador = Nominatim(user_agent="mi_app2") 

    try:
        ubicacion = geolocalizador.reverse((latitud, longitud), language="es") 
        if ubicacion:
            return ubicacion.address
        else:
            return "No se encontró información de ubicación para estas coordenadas."
    except GeocoderTimedOut:
        print("Tiempo de espera agotado. Reintentando en 5 segundos...")
        time.sleep(5)
        return region(latitud, longitud)
    except GeocoderServiceError as e:
        print(f"Error en el servicio de geocodificación: {str(e)}")
        ubicacion_2 = region2(latitud, longitud)
        return ubicacion_2
    


def create_pdf(rgb, ndvi, ironO, alunite, FEOOH, AAI, AIS, DOS, name, folder, bbox, image_date):

    print('Generating Report...')

    name = name.replace('.nc','.pdf')

    pdf_file = './data/' + folder + '/' + name

    can = canvas.Canvas(pdf_file)

    # ==== IMAGEN ====
    width, height = letter
    imgr = plt.imread(rgb)
    h, w, _ = imgr.shape
    x = ((width-(w*0.21))//2)
    y = ((height-(h*0.21))//2)
    can.drawImage(rgb, x, y, w*0.21, h*0.21)
    # ================

    # Dibujar el rectángulo rojo
    can.setStrokeColorRGB(1, 1, 1)  # Establecer color de contorno rojo (1, 0, 0)
    can.setFillColorRGB(1, 1, 1)  # Establecer color de relleno rojo (1, 0, 0)
    can.rect(-1, 720, 700, 150, fill=True, stroke=True)  # Rectángulo rojo
    
    can.setStrokeColorRGB(0, 0, 0)  # Establecer color de contorno
    can.setFillColorRGB(0, 0, 0)    # Establecer color de relleno
    can.line(0, 720, 600, 720)      # Horizontal
    can.line(140, 790, 600, 790)    # Horizontal
    can.line(140, 720, 140, 850)    # Vertical

    # Para titulos asignamos una fuente y el tamaño = 20
    can.setFont('Helvetica', 20)

    # Dibujamos texto: (X,Y,Texto)
    can.drawString(150,810,"NASA SpaceApp Geology 2023")

    # Para parrafos normales cambiamos el tamaño a 12
    can.setFont('Helvetica', 12)

    # Dibujamos texto: (X,Y,Texto)
    p1,p2,p3,p4 = bbox
    can.drawString(145,775,"Image Name:    " + name)
    can.drawString(145,760,"Image Date Set: " + image_date)
    can.drawString(145,745,f"Lat | Lon:  {p1} | {p2}")
    ubicacion = region(p2, p1)
    can.setFont('Helvetica', 10)
    can.drawString(145,730,"Zone: " + ubicacion)
    can.setFont('Helvetica', 12)

    # Dibujamos una imagen (IMAGEN, X,Y, WIDTH, HEIGH)
    can.drawImage('./Logo.png', 20, 735, 100, 90)
    can.showPage()
    
    # --- Page 2 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"NDVI:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine('NDVI, or Normalized Difference Vegetation Index, is an indicator used to assess the health and density')
    text.textLine('of vegetation in terrestrial areas from satellite and remote sensing data.')
    text.textLine('is commonly used in agriculture, ecology and environmental studies to monitor crop growth, forest health') 
    text.textLine('and vegetation in general. It is especially useful in the early detection of drought, water stress and') 
    text.textLine('changes in vegetation cover.')
    can.drawText(text)

    imgr = plt.imread(ndvi)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(ndvi, x, y, w*0.20, h*0.20)
    can.showPage()
    
    # --- Page 3 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"Iron Oxide Index:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("Is a hyperspectral index used in the analysis of satellite or aerial imagery to identify the presence and") 
    text.textLine("concentration of iron minerals on the earth's surface. These minerals include iron oxides such as hematite") 
    text.textLine("(Fe2O3) and goethite (FeO(OH)), which are important in the mining industry because of their economic value.")
    can.drawText(text)

    imgr = plt.imread(ironO)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(ironO, x, y, w*0.20, h*0.20)
    can.showPage()

    # --- Page 4 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"AlOH:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("The aluminum hydroxylated (AlOH) absorption index is a hyperspectral index used in satellite or aerial image") 
    text.textLine("analysis to detect the presence and concentration of minerals containing hydroxylated aluminum, such as ")
    text.textLine("kaolinite (a clay mineral) and alunite. These minerals are important in the mining industry and in geological") 
    text.textLine("studies because of their relationship to geological processes and the formation of mineral deposits.") 
    can.drawText(text)

    imgr = plt.imread(alunite)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(alunite, x, y, w*0.20, h*0.20)
    can.showPage()

    # --- Page 5 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"FEOOH:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("The Ferric Oxide-Oxyhydroxide Clay Index (FEOOH) is a hyperspectral index used in satellite or airborne image ")
    text.textLine("analysis to detect the presence and concentration of clay minerals containing ferric oxides and oxyhydroxides.") 
    text.textLine("This index is particularly useful for identifying the presence of minerals such as goethite and hematite, which")
    text.textLine("are common iron minerals present in geological formations.") 
    can.drawText(text)

    imgr = plt.imread(FEOOH)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(FEOOH, x, y, w*0.20, h*0.20)
    can.showPage()

    # --- Page 6 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"Clay Alteration Index:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("The Clay Alteration Index is a hyperspectral index used in satellite or airborne image analysis to identify") 
    text.textLine("the presence and concentration of clay minerals in geological formations. Clay minerals are important indicators") 
    text.textLine("of hydrothermal alteration and are often associated with mineral deposits and reservoirs.")
    can.drawText(text)

    imgr = plt.imread(AAI)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(AAI, x, y, w*0.20, h*0.20)
    can.showPage()

    # --- Page 7 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"Argillic and Sericitic Alteration Index:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("The Argillic and Sericite Alteration Index is a hyperspectral index used in satellite or aerial image analysis") 
    text.textLine("to identify the presence and concentration of clay minerals and sericite in geological formations. Both clay") 
    text.textLine("minerals and sericite are indicators of hydrothermal alteration processes and are often associated with mineral") 
    text.textLine("deposits and reservoirs.") 
    can.drawText(text)

    imgr = plt.imread(AIS)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(AIS, x, y, w*0.20, h*0.20)
    can.showPage()

    # --- Page 8 ---
    can.setFont('Helvetica', 16)
    can.drawString(40,770,"Deep Contour Iron Oxide Index:")

    can.setFont('Helvetica', 10)
    text = can.beginText(40, 750)

    text.textLine("The Deep Contour Iron Oxide Index, is a hyperspectral index used in satellite or airborne image analysis to identify") 
    text.textLine("the presence and concentration of iron oxides in geological formations. Iron oxides, such as hematite and goethite,") 
    text.textLine("are important minerals for industry and can also be indicators of specific geological processes.") 
    can.drawText(text)

    imgr = plt.imread(DOS)
    h, w, _ = imgr.shape
    x = ((width-(w*0.20))//2)
    y = ((height-(h*0.20))//2)
    can.drawImage(DOS, x, y, w*0.20, h*0.20)
    can.showPage()
 
    can.save()

    # Delete files
    ruta = './data/' + folder

    archivos = os.listdir(ruta)

    for archivo in archivos:
        if archivo.endswith(".png"):
            archivo_ruta = os.path.join(ruta, archivo) 
            os.remove(archivo_ruta)

 


def mineral_data(group_band_1, group_id_1, group_band_2, group_id_2, folder, name_img_mineral):

    print('Masking Data Image...')

    folder = os.path.join('./data',folder)

    for i in range(2):
        if i == 0:
            group_id_1 = group_id_1
            group_band_1 = group_band_1
            name_band = folder + '/' + name_img_mineral + '_group_1_band_depth.png'
            name_id = folder + '/' + name_img_mineral + '_group_1_mineral_id.png'
        else:
            group_id_1 = group_id_2
            group_band_1 = group_band_2
            name_band = folder + '/' + name_img_mineral + '_group_2_band_depth.png'
            name_id = folder + '/' + name_img_mineral + '_group_2_mineral_id.png'

        # ====== ID ======
        # Obtiene los valores únicos de la matriz y sus colores correspondientes
        valores_unicos = np.unique(group_id_1)
        colores = plt.cm.get_cmap('tab20', len(valores_unicos))

        # Crea una lista de parches y etiquetas para la leyenda
        patches = []
        labels = []

        for valor, color in zip(valores_unicos, colores(np.arange(len(valores_unicos)))):
            # Crea un parche cuadrado con el color correspondiente
            square = Patch(color=color, label=str(valor))
            patches.append(square)
            labels.append(str(valor))

        # Plotea la matriz como una imagen y ajusta el aspecto para que los cuadrados sean cuadrados
        plt.subplots(figsize=(30,30))
        plt.imshow(group_id_1, cmap='tab20', aspect='equal')
        plt.legend(handles=patches, labels=labels, loc='upper left', bbox_to_anchor=(1, 1))
        plt.axis('off')
        plt.savefig(name_id, bbox_inches='tight')
        plt.close()

        # ====== BAND ======
        # Plot
        plt.subplots(figsize=(30,30))
        plt.imshow(group_band_1, cmap='inferno')
        plt.axis('off')
        plt.savefig(name_band, bbox_inches='tight')
        plt.close()