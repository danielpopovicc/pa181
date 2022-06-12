#!/usr/bin/env python
# coding: utf-8

# In[2]:


import geopandas
import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import Point


# In[3]:


fields = gpd.read_file('assets/brownfields.geojson')
fields = fields[['geometry', 'kontaminace_lokality', 'skladky']]
df = pd.read_csv('assets/adresní_místa___Address_points.csv')


# In[36]:


fields = fields[(fields['kontaminace_lokality'] == 'Ano') | (fields['skladky'] == 'Ano')]


# In[75]:


fields_buffered = GeoSeries.to_crs(fields['geometry'], crs='EPSG:4326').buffer(0.002)


# In[76]:


df['point'] = df.apply(lambda address: Point(address.X, address.Y), axis=1)
points = geopandas.GeoSeries(df['point'], crs=4326)


# In[77]:


addresses_nearby_field = fields_buffered.apply(lambda field: points.within(field))


# In[78]:


t = addresses_nearby_field.transpose()


# In[79]:


addresses_meeting_criteria = t.loc[(t == True).any(axis=1)]


# In[84]:


num_of_addresses_nearby = addresses_meeting_criteria.apply(lambda address: address[address == True].count(), axis=1)


# In[83]:


num_of_addresses_nearby.to_csv('brownfields.csv')

