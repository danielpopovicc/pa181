import geopandas
from geopandas import GeoSeries
import pandas as pd
from shapely.geometry import Point


def get_kindergarden_data():
    gpd_skolky = geopandas.read_file('../assets/skolky.geojson')
    addresses = pd.read_csv('../assets/adresní_místa___Address_points.csv')
    kinder_buffered = GeoSeries.to_crs(gpd_skolky['geometry'], crs=4326).buffer(0.005)
    addresses['point'] = addresses.apply(lambda address: Point(address.X, address.Y), axis=1)
    points = geopandas.GeoSeries(addresses['point'], crs=4326)

    addresses_with_schools = kinder_buffered.apply(lambda school: points.within(school))
    t = addresses_with_schools.transpose()

    at_least_one_school_nearby = t.loc[(t == True).any(axis=1)]

    # num_of_schools= filtered_addresses.apply(lambda address: address[address==True].index, axis=1)

    # index == index of address
    num_of_schools_nearby = at_least_one_school_nearby.apply(lambda address: address[address == True].count(), axis=1)
    num_of_schools_nearby.index.name = 'address_idx'
    num_of_schools_nearby.name = 'count_of_kindergardens'
    num_of_schools_nearby.to_csv('dataset_outputs/skolky.csv', header=False)


get_kindergarden_data()
