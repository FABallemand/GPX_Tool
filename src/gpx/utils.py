import os
import gpxpy
import gpxpy.gpx
import gpxpy.geo
import pandas as pd
import matplotlib.pyplot as plt

from ..app.logger import emitLog, Log

def openGPX(file_path):
    """
    Open and read a GPX file.

    Args:
        file_path (str): Path of the file to read.

    Returns:
        GPX: Content of the GPX file.
    """
    gpx = None
    try:
        with open(file_path, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except OSError:
        emitLog(Log.ERROR, "Unable to open file: " + file_path)
    return gpx

def saveGPX(gpx, file_path):
    """
    Save GPX to file.

    Args:
        gpx (GPX): GPX object.
        file_path (str): Path of the file to write in.
    """
    try:
        file = open(file_path, "w")
        file.write(gpx.to_xml())
        file.close()
    except:
        emitLog(Log.ERROR, f"Unable to save GPX {file_path}")

def visualizeGPX(file_path, base_color="#101010", elevation_color=False):
    """
    Visualize GPX file.

    Args:
        file_path (str): File path.
        base_color (str, optional): Base color. Defaults to "#101010".
        elevation_color (bool, optional): If set to True, color track points according to elevation. Defaults to False.
    """
    # Read GPX file
    gpx = openGPX(file_path)

    # Create dataframe containing data from the GPX file
    route_info = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                route_info.append({
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "elevation": point.elevation
                })
    route_df = pd.DataFrame(route_info)

    # Visualize GPX file
    plt.figure(figsize=(14, 8))
    if elevation_color:
        plt.scatter(route_df["longitude"], route_df["latitude"], color=route_df["elevation"])
    else:
        plt.scatter(route_df["longitude"], route_df["latitude"], color=base_color)
    plt.title("Track", size=20)