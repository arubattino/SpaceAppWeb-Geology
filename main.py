import os
import service
import netCDF4 as nc
import argparse
import warnings
warnings.filterwarnings("ignore")



def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--u', type=str, required=True, help='')
    parser.add_argument('--p', type=str, required=True, help='')
    parser.add_argument('--d', type=str, required=True, help='')
    parser.add_argument('--bx', type=str, required=True, help='')
    
    args = parser.parse_args()
    
    user = args.u
    password = args.p
    date = args.d
    latlon = args.bx

    x, y = date.split(',')
    date = (x,y)

    latlon = latlon.replace('"','')
    latlon = latlon.replace("'","")
    l1,l2,l3,l4 = latlon.split(',')
    bx = (l1,l2,l3,l4)

    print('\nInitializing...\n')
    
    try: 
        folder_name, name_image, date_image  = service.download_data_EMIT(user, password, bx, date, 'EMITL2ARFL')

        nc_file = os.path.join('./data/'+folder_name, name_image)
        service.analysis(nc_file, './data/'+folder_name)

        service.create_pdf('./data/'+folder_name+'/rgb.png',
                            './data/'+folder_name+'/ndvi.png',
                            './data/'+folder_name+'/iron_oxide.png',
                            './data/'+folder_name+'/alunite.png',
                            './data/'+folder_name+'/FEOOH.png',
                            './data/'+folder_name+'/AAI.png',
                            './data/'+folder_name+'/AIS.png',
                            './data/'+folder_name+'/DOS.png',
                            name_image,
                            folder_name,
                            bx,
                            date_image)

        _, name_image, date_image  = service.download_data_EMIT(user,password, bx, date, 'EMITL2BMIN')

        nc_file = os.path.join('./data/'+folder_name, name_image)

        name_img_mineral = os.path.basename(nc_file)
        name_img_mineral = (name_img_mineral[:-3])

        ds = nc.Dataset(nc_file)

        group_1_band_depth = ds.variables['group_1_band_depth'][:]
        group_1_mineral_id = ds.variables['group_1_mineral_id'][:]
        group_2_band_depth = ds.variables['group_2_band_depth'][:]
        group_2_mineral_id = ds.variables['group_2_mineral_id'][:]

        service.mineral_data(group_1_band_depth, group_1_mineral_id, group_2_band_depth, group_2_mineral_id, folder_name, name_img_mineral)

        print('\n --- Finished processing --- \n')

    except:
        print("\n --- No data found --- \n")

if __name__ == "__main__":
    main()