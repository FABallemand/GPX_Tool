import os
import gpxpy
import gpxpy.gpx
import gpxpy.geo

def removeGPSErrors(gpx, error_distance=1000):
    """
    Remove GPS errors.

    Args:
        gpx (GPX): GPX object.
        error_distance (int, optional): GPS error threshold distance (in meters) between two points. Defaults to 1000.

    Returns:
        GPX: GPX object without GPS error.
        list: List of removed points (GPS errors).
    """
    # Create new "file"
    cleaned_gpx = gpxpy.gpx.GPX()

    previous_point = None
    GPS_errors = []

    for track in gpx.tracks:
        # Create track
        gpx_track = gpxpy.gpx.GPXTrack()
        cleaned_gpx.tracks.append(gpx_track)
        for segment in track.segments:
            # Create segment
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            for point in segment.points:
                # Create points
                if previous_point is None or gpxpy.geo.haversine_distance(previous_point.latitude,
                                                                          previous_point.longitude,
                                                                          point.latitude,
                                                                          point.longitude) < error_distance:
                    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(point.latitude, point.longitude, elevation=point.elevation))
                    previous_point = point
                else:
                    GPS_errors.append(point)
    return cleaned_gpx, GPS_errors


def compressFile(gpx, compression_method="Ramer-Douglas-Peucker algorithm", vertical_smooth=True, horizontal_smooth=True):
    """
    Compress GPX file.

    Args:
        gpx (GPX): GPX object.
        compression_method (str, optional): Method used to compress GPX. Defaults to "RPD".
        vertical_smooth (bool, optional): Vertical smoothing. Defaults to True.
        horizontal_smooth (bool, optional): Horizontal smoothing. Defaults to True.

    Returns:
        GPX: Compressed GPX object.
    """
    # Smoothing
    gpx.smooth(vertical=vertical_smooth, horizontal=horizontal_smooth)

    # Compression
    if compression_method == "Ramer-Douglas-Peucker algorithm":
        gpx.simplify()
    elif compression_method == "Remove 25% points":
        gpx.reduce_points(int(gpx.get_track_points_no() * 0.75))
    elif compression_method == "Remove 50% points":
        gpx.reduce_points(int(gpx.get_track_points_no() * 0.5))
    elif compression_method == "Remove 75% points":
        gpx.reduce_points(int(gpx.get_track_points_no() * 0.25))
        
    return gpx