import pandas as pd
from collections import deque
import sys
import streamlit as st
import osmnx as ox
import requests
import folium
from streamlit_folium import folium_static
import time  

def load_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        print("File tidak ditemukan. Silakan periksa jalur file.")
        sys.exit(1)

def create_graph(data, selected_cities):
    filtered_cities = data[data['Kota/Kab'].isin(selected_cities)]
    cities = list(filtered_cities['Kota/Kab'])
    graph = {}

    for city1 in cities:
        graph[city1] = {}
        for city2 in cities:
            if city1 != city2:
                try:
                    distance = data.loc[data['Kota/Kab'] == city1, city2].values[0]
                    graph[city1][city2] = distance
                except IndexError:
                    graph[city1][city2] = float('inf')

    return graph

def path_cost_function(path, adj, start_city):
    cost = 0
    for i in range(len(path) - 1):
        city_from = path[i]
        city_to = path[i + 1]
        cost += adj[city_from][city_to]
    cost += adj[path[-1]][start_city]  
    return cost

def bfs(adj, start_city):
    cities = list(adj.keys())
    s = cities.index(start_city)
    visited = [False] * len(adj)
    path = []
    min_path = []
    min_cost = [float('inf')]
    q = deque([s])
    visited[s] = True
    operation_count = 0 
    node_count = 0  
    edge_count = 0  

    while q:
        curr = q.popleft()
        current_city = cities[curr]
        path.append(current_city)
        operation_count += 1  
        node_count += 1 

        if len(path) == len(adj):  
            path_cost = path_cost_function(path, adj, start_city)
            if path_cost < min_cost[0]:
                min_cost[0] = path_cost
                min_path[:] = path[:]
          
            edge_count += 1  

        for neighbor in adj[current_city]:
            neighbor_index = cities.index(neighbor)
            if not visited[neighbor_index]:
                visited[neighbor_index] = True
                operation_count += 1 
                edge_count += 1 
                q.append(neighbor_index)

    memory_usage = sys.getsizeof(visited) + sys.getsizeof(path) + sys.getsizeof(q)
    return min_path, min_cost[0], memory_usage, operation_count, node_count, edge_count

def dfs_rec(adj, visited, current_city, path, min_path, min_cost, start_city, node_count, edge_count, operation_count):
    visited[current_city] = True
    path.append(current_city)
    node_count[0] += 1  
    operation_count[0] += 1  

    if len(path) == len(adj):  
        path_cost = path_cost_function(path, adj, start_city)
        if path_cost < min_cost[0]:
            min_cost[0] = path_cost
            min_path[:] = path[:]
            operation_count[0] += 1  
        edge_count[0] += 1  

    for neighbor in adj[current_city]:
        edge_count[0] += 1  
        operation_count[0] += 1  
        if not visited[neighbor]:
            dfs_rec(adj, visited, neighbor, path, min_path, min_cost, start_city, node_count, edge_count, operation_count)

    visited[current_city] = False
    path.pop()
    operation_count[0] += 1  

def dfs(adj, start_city):
    visited = {city: False for city in adj}
    path = []
    min_path = []
    min_cost = [float('inf')]
    node_count = [0]  
    edge_count = [0]  
    operation_count = [0]  
    dfs_rec(adj, visited, start_city, path, min_path, min_cost, start_city, node_count, edge_count, operation_count)

    # Menghitung penggunaan memori
    memory_usage = sys.getsizeof(visited) + sys.getsizeof(path)
    return min_path, min_cost[0], memory_usage, operation_count[0], node_count[0], edge_count[0]

def get_coordinates(city_name):
    if city_name.lower() == "gresik":
        return (-7.1667, 112.6403)  
    else:
        location = ox.geocode(city_name)
        return location 

def get_route_osrm(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'routes' in data and len(data['routes']) > 0:
            route = data['routes'][0]['geometry']['coordinates']
            return route
        else:
            return None
    else:
        return None

def visualize_route(route, coordinates):
    start_location = coordinates[route[0]]
    m = folium.Map(location=start_location, zoom_start=8)

    for i in range(len(route) - 1):
        start_city = route[i]
        end_city = route[i + 1]
        route_coords = get_route_osrm(coordinates[start_city], coordinates[end_city])
        
        if route_coords:
            folium.PolyLine([(coord[1], coord[0]) for coord in route_coords], color='blue', weight=4, opacity=0.6).add_to(m)

    for city in route:
        folium.Marker(location=coordinates[city], popup=city).add_to(m)

    return m

def main():
    st.title("Optimal Path Finder")


    file_path = r'C:\Users\Theopan gerard\OneDrive\Documents\Tugas_DAA\Project\jalur_clean.csv'
    data = load_data(file_path)

    
    cities = data.columns.tolist()

    
    selected_cities = st.multiselect("Pilih kota (minimal 10 kota):", cities, default=cities[:10])

    if len(selected_cities) < 10:
        st.warning("Silakan pilih minimal 10 kota.")
        return

    st.write(f"Kota yang dipilih: {selected_cities}")

    
    graph = create_graph(data, selected_cities)

   
    start_city = st.selectbox("Masukkan kota awal:", selected_cities)

    if start_city not in graph:
        st.error("Kota awal tidak ditemukan dalam graf.")
        st.write(f"Kota yang tersedia: {list(graph.keys())}")
        return

 
    algorithm = st.selectbox("Pilih algoritma:", ["BFS", "DFS"])

    
    if algorithm == "BFS":
        start_time = time.time()  
        min_path, min_cost, memory_usage,operasi,node_count,edge_count = bfs(graph, start_city)
        execution_time = time.time() - start_time   
    else:
        start_time = time.time()  
        min_path, min_cost, memory_usage, node_count, edge_count,operasi = dfs(graph, start_city)
        execution_time = time.time() - start_time  
    st.write("\nJalur optimal:")
    st.write(" -> ".join(min_path + [start_city]))
    st.write(f'Total Jarak perjalanan: {min_cost} Km') 
    st.write(f'Waktu eksekusi: {execution_time:.4f} detik')
    st.write(f'Penggunaan memori (kompleksitas ruang): {memory_usage} bytes')
    st.write(f'Operasi yang dilakukan: {operasi}')
    st.write(f'Jumah Node yang dikunjungi: {node_count}')
    st.write(f'Jumlah edge yang di kunjungi: {edge_count}')

    
    city_coordinates = {}
    for city in selected_cities:
        coords = get_coordinates(city)
        city_coordinates[city] = coords

    
    map_route = visualize_route(min_path + [start_city], city_coordinates)
    
    
    st.write("Peta Rute:")
    folium_static(map_route)

if __name__ == "__main__":
    main()
