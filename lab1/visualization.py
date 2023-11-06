from typing import Tuple
import numpy as np
import open3d as o3d
import cv2

# Visualization functions

def show(objects_to_draw, boxes_color: np.ndarray = None, **kwargs) -> None:
        
    if 'view_point' in kwargs:
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        vis.clear_geometries()
        for obj in objects_to_draw:
            vis.add_geometry(obj)

        if kwargs['view_point'] is not None:
            ctr = vis.get_view_control()
            ctr.set_front(kwargs['view_point']['front'])
            ctr.set_lookat(kwargs['view_point']['lookat'])
            ctr.set_up(kwargs['view_point']['up'])
            ctr.set_zoom(kwargs['view_point']['zoom'])
            

        vis.get_render_option().point_size = 2.0
        vis.update_renderer()         
        vis.poll_events()
        if 'save_to_path' in kwargs:
            vis.capture_screen_image(kwargs['save_to_path'])
    else:
        o3d.visualization.draw_geometries(objects_to_draw)
        

def create_cube_o3d(corners: np.ndarray, color: Tuple[float] = None):
    """
    Create a box to be visualized using open3d. Convention
    forward face: 0 - 1 - 2 - 3, backward face: 4 - 5 - 6 - 7, top face: 0 - 4 - 5 - 1
    :param corners: (8, 3) - coordinate of 8 corners
    :param color: color of the cube
    :return:
    """
    lines = [
        [0, 1], [1, 2], [2, 3], [3, 0],  # front
        [4, 5], [5, 6], [6, 7], [7, 4],  # back
        [0, 4], [1, 5], [2, 6], [3, 7],  # connecting front & back
        [0, 2], [1, 3]  # denote forward face
    ]
    if color is None:
        colors = [[1, 0, 0] for _ in range(len(lines))]  # red
    else:
        colors = [color for _ in range(len(lines))]
    cube = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(corners),
        lines=o3d.utility.Vector2iVector(lines),
    )
    cube.colors = o3d.utility.Vector3dVector(colors)
    return cube


def box_to_corner(box: np.ndarray) -> np.ndarray:  #TO DO
    """
    Compute coordinate of box's corners. Convention
    forward face: 0 - 1 - 2 - 3, backward face: 4 - 5 - 6 - 7, top face: 0 - 4 - 5 - 1

    :param box: (7) - center_x, center_y, center_z, dx, dy, dz, yaw
    :return: (8, 3)
    """
    assert box.shape == (7,), f"expect (7,), get {box.shape}"
    # TODO: compute coordinate of 8 corners in the frame relative to which the `box` is expressed
    # TODO: Notice the order of 8 corners must be according to the convention stated the function doc string
    x, y, z, w, l, h,  yaw = box
    dx = w / 2
    dy = l / 2
    dz = h / 2
    cos = np.cos(-yaw)
    sin = np.sin(-yaw)
    corners = np.array([[x + dx*cos + dy*sin , y + dy*cos - dx*sin, z+dz ],
                        [x + dx*cos - dy*sin , y - dy*cos - dx*sin, z+dz ],
                        [x + dx*cos - dy*sin , y - dy*cos - dx*sin, z-dz  ],
                        [x + dx*cos + dy*sin , y + dy*cos - dx*sin, z -dz ],
                        [x - dx*cos + dy*sin , y + dy*cos + dx*sin, z+dz ],
                        [x - dx*cos - dy*sin , y - dy*cos + dx*sin, z+dz ],
                        [x - dx*cos - dy*sin , y - dy*cos + dx*sin, z-dz  ],
                        [x - dx*cos + dy*sin , y + dy*cos + dx*sin, z-dz ]])  
    # corners = np.zeros((8, 3))# this is just a dummy value
    
    return corners


def show_point_cloud(points: np.ndarray, boxes: np.ndarray = None, point_colors: np.ndarray = None,
                     box_colors: np.ndarray = None):
    """
    Visualize point cloud
    :param points: (N, 3) - x, y, z
    :param boxes: (B, 7) - center_x, center_y, center_z, dx, dy, dz, yaw
    :param point_colors: (N, 3) - r, g, b
    :param box_colors: (B, 3) - r, g, b
    """
    assert points.shape[1] == 3, f"expect (N, 3), get {points.shape}"
    # assert boxes.shape[1] == 7, f"expect (B, 7), get {boxes.shape}"
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    if point_colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(point_colors)

    frame = o3d.geometry.TriangleMesh.create_coordinate_frame()
    obj_to_display = [pcd]

    if boxes is not None:
        cubes = [create_cube_o3d(box_to_corner(boxes[i]), box_colors[i] if box_colors is not None else None)
                 for i in range(boxes.shape[0])]
        obj_to_display += cubes

    o3d.visualization.draw_geometries(obj_to_display)

def box_vel(centers: np.ndarray, vel: np.ndarray, theta) -> np.ndarray:
    delta_x = vel[0] * 0.5
    delta_y = vel[1] * 0.5
    cos = np.cos(theta)
    sin = np.sin(theta)
    tip = [centers[0]+ delta_x * cos + delta_y * sin ,centers[1] + delta_y * cos - delta_x * sin ]  # [x, y]
    tip.append(centers[-1])  # z
    pts = np.stack([centers, np.array(tip)], axis=0)
    o3d_displacement_line = o3d.geometry.LineSet(
        points=o3d.utility.Vector3dVector(pts),
        lines=o3d.utility.Vector2iVector([[0, 1]]),
    )
    return o3d_displacement_line


def show_objects(ptcloud, boxes, colors):
    obj_to_draw = []
    # Plot Lidar point_cloud in world frame
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(ptcloud)
    obj_to_draw.append(pcd)
    
    

    # Plot bounding boxes
    if boxes is not None:
        cubes = [create_cube_o3d(box_to_corner(boxes[i]), colors[i] if colors is not None else None)
                 for i in range(boxes.shape[0])]
        obj_to_draw += cubes
    # show
    show(obj_to_draw)

def box_to_pixels(boxes, bev_imsize, bev_resolution):
    # box: (1,8) : (cx, cy, cz, l, w, h, yaw)
    # return: pixel coordinates within the box np.ndarray

    corners = [box_to_corner(boxes[i])for i in range(boxes.shape[0])]
    # Take only bev 
    corners = np.array(corners)
    top = [0,4,5,1]
    corners = corners[:, top, :2]

    
    # Find the pixel coordinates of the corners
    pixel_coordinates = []
    for corner in corners:
        corner = (corner / bev_resolution + bev_imsize / 2).astype(int)

        # fill pixels within corners
        pixel_coordinates.append(corner)
    # create mask to get all pixels occupied within corners
    mask = np.zeros(bev_imsize, dtype=np.uint8)
    cv2.fillPoly(mask, np.array(pixel_coordinates), 255)
    
    return mask

def points_to_pixels(filtered_points, bev_imsize, bev_resolution):
    # filtered_points: (N, 3) : (x, y, z)
    # return: pixel coordinates within the box np.ndarray

    # Take only bev 
    bev_points = filtered_points[:, :2]
    
    # Find the pixel coordinates of the points
    bev_pixels = (bev_points /bev_resolution + bev_imsize / 2).astype(int)
    
    
    return bev_pixels