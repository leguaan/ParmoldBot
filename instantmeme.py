import discord
import random
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates
import io
import logging
import traceback

OVERLAYS_FOLDER = 'data/faces'

async def try_handle_instant_meme(message):
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                logging.debug('try_handle_instant_meme', extra={'message_content': message.content, 'message_id': message.id})
                async with message.channel.typing():
                    img = await get_img_from_attachment(attachment)
                    faces = get_faces(img)

                    if not faces.multi_face_landmarks:
                        logging.info('Message {message_id} didnt contain any faces', message_id=message.id)
                        return None

                    points_on_faces = get_specific_points_on_faces(img, faces)
                    logging.debug('Points on faces {pts}', pts=points_on_faces, extra={'message_id': message.id})

                    for face in points_on_faces:
                        overlay_filename = random.choice(os.listdir(OVERLAYS_FOLDER))
                        overlay_path = os.path.join(OVERLAYS_FOLDER, overlay_filename)

                        overlay = get_img_from_path(overlay_path)
                        overlay_faces = get_faces(overlay, no_of_faces=1)
                        points_on_overlay_faces = get_specific_points_on_faces(overlay, overlay_faces)
                        logging.debug('Points on overlay faces {pts}', pts=points_on_overlay_faces, extra={'message_id': message.id})

                        p1_src = np.array(points_on_overlay_faces[0][0])
                        p2_src = np.array(points_on_overlay_faces[0][1])

                        p1_dst = np.array(face[0])
                        p2_dst = np.array(face[1])

                        A = np.array([
                            [p1_src[0], -p1_src[1], 1, 0],
                            [p1_src[1],  p1_src[0], 0, 1],
                            [p2_src[0], -p2_src[1], 1, 0],
                            [p2_src[1],  p2_src[0], 0, 1]
                        ])

                        b = np.array([p1_dst[0], p1_dst[1], p2_dst[0], p2_dst[1]])

                        params, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
                        a, b_param, tx, ty = params

                        M = np.array([
                            [a, -b_param, tx],
                            [b_param,  a, ty]
                        ])

                        rows, cols = img.shape[:2]
                        transformed_overlay = cv2.warpAffine(overlay, M, (cols, rows))

                        y1, y2 = 0, 0 + transformed_overlay.shape[0]
                        x1, x2 = 0, 0 + transformed_overlay.shape[1]

                        alpha_s = transformed_overlay[:, :, 3] / 255.0
                        alpha_l = 1.0 - alpha_s

                        for c in range(0, 3):
                            img[y1:y2, x1:x2, c] = (alpha_s * transformed_overlay[:, :, c] +
                                                    alpha_l * img[y1:y2, x1:x2, c])
                        
                    await send_img_to_channel(img, message.channel)


def get_img_from_path(path):
    return cv2.imread(path, -1)

async def get_img_from_attachment(attachment):
    img_bytes = await attachment.read()
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
    return img;


def get_faces(img, no_of_faces = 10):
    face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=no_of_faces,
            refine_landmarks=True,
            min_detection_confidence=0.5)
    faces = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return faces


def draw_masks_on_faces(img, faces):
    image_rows, image_cols, _ = img.shape
    for face in faces.multi_face_landmarks:
        for mask_point in face.landmark:
            cord = _normalized_to_pixel_coordinates(mask_point.x,mask_point.y,image_cols,image_rows)
            cv2.putText(img, '.', cord,cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 2)

def draw_specific_points_on_faces(img, faces, points = [33, 263]):
    image_rows, image_cols, _ = img.shape
    for face in faces.multi_face_landmarks:
        all_points = face.landmark
        for mask_point in points:
            cord = _normalized_to_pixel_coordinates(all_points[mask_point].x,all_points[mask_point].y,image_cols,image_rows)
            cv2.putText(img, '.', cord,cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 2)

def get_specific_points_on_faces(img, faces, points = [33, 263]):
    points_on_faces = []
    image_rows, image_cols, _ = img.shape
    for face in faces.multi_face_landmarks:
        all_points = face.landmark
        points_on_face = []
        for mask_point in points:
            cord = _normalized_to_pixel_coordinates(all_points[mask_point].x,all_points[mask_point].y,image_cols,image_rows)
            points_on_face.append(cord)
        points_on_faces.append(points_on_face)
    return points_on_faces

def draw_points_on_faces(img, points_on_faces):
    for face in points_on_faces:
        for point in face:
            cv2.putText(img, '.', point,cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 2)
            

async def send_img_to_channel(img, channel):
    _, buffer = cv2.imencode('.png', img)
    output_bytes = buffer.tobytes()
    await channel.send(file=discord.File(fp=io.BytesIO(output_bytes), filename='output.png'))


async def process_image(img):
    mp_face_mesh = mp.solutions.face_mesh

    with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5) as face_mesh:

        # Convert the BGR image to RGB before processing.
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            # No faces detected, skip the image
            return None

        # For each face detected
        for face_landmarks in results.multi_face_landmarks:
            # Get eye and mouth landmarks
            left_eye_points = [(face_landmarks.landmark[idx].x * img.shape[1],
                                face_landmarks.landmark[idx].y * img.shape[0]) for idx in LEFT_EYE_INDICES]
            right_eye_points = [(face_landmarks.landmark[idx].x * img.shape[1],
                                 face_landmarks.landmark[idx].y * img.shape[0]) for idx in RIGHT_EYE_INDICES]
            mouth_points = [(face_landmarks.landmark[idx].x * img.shape[1],
                             face_landmarks.landmark[idx].y * img.shape[0]) for idx in MOUTH_INDICES]

            # Ensure eye points are detected
            if not left_eye_points or not right_eye_points:
                continue  # Skip if eyes are not detected

            left_eye_center = np.mean(left_eye_points, axis=0)
            right_eye_center = np.mean(right_eye_points, axis=0)
            mouth_center = np.mean(mouth_points, axis=0)
            target_midpoint = (left_eye_center + right_eye_center) / 2

            # Pick a random overlay image
            overlay_filename = random.choice(os.listdir(OVERLAYS_FOLDER))
            overlay_path = os.path.join(OVERLAYS_FOLDER, overlay_filename)
            overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)

            flip_vertical = random.choice([True, False])
            if flip_vertical:
                overlay_img = cv2.flip(overlay_img, 1)  # Flip vertically

            # Resize the overlay image to a similar size as the detected face
            face_width = int(distance(left_eye_center, right_eye_center) * 1.5)
            overlay_img = cv2.resize(overlay_img, (face_width, face_width))

            # Process overlay image with face mesh
            overlay_results = face_mesh.process(cv2.cvtColor(overlay_img, cv2.COLOR_BGR2RGB))

            if not overlay_results.multi_face_landmarks:
                continue  # Skip if no landmarks are found in overlay

            overlay_face_landmarks = overlay_results.multi_face_landmarks[0]

            # Get eye landmarks in overlay image
            overlay_left_eye_points = [(overlay_face_landmarks.landmark[idx].x * overlay_img.shape[1],
                                        overlay_face_landmarks.landmark[idx].y * overlay_img.shape[0]) for idx in
                                       LEFT_EYE_INDICES]
            overlay_right_eye_points = [(overlay_face_landmarks.landmark[idx].x * overlay_img.shape[1],
                                         overlay_face_landmarks.landmark[idx].y * overlay_img.shape[0]) for idx in
                                        RIGHT_EYE_INDICES]
            overlay_mouth_points = [(overlay_face_landmarks.landmark[idx].x * overlay_img.shape[1],
                                     overlay_face_landmarks.landmark[idx].y * overlay_img.shape[0]) for idx in
                                    MOUTH_INDICES]

            if not overlay_left_eye_points or not overlay_right_eye_points:
                continue  # Skip if overlay eyes are not detected

            overlay_left_eye_center = np.mean(overlay_left_eye_points, axis=0)
            overlay_right_eye_center = np.mean(overlay_right_eye_points, axis=0)
            overlay_midpoint = (overlay_left_eye_center + overlay_right_eye_center) / 2

            # Compute the average angle for the target face
            target_face_angle = compute_face_angle(left_eye_center, right_eye_center, mouth_points[0], mouth_points[1])
            # Compute the average angle for the overlay face
            overlay_face_angle = compute_face_angle(overlay_left_eye_center, overlay_right_eye_center,
                                                    overlay_mouth_points[0], overlay_mouth_points[1])
            # Calculate the angle difference for transformation
            angle = target_face_angle - overlay_face_angle

            overlay_eye_distance = distance(overlay_left_eye_center, overlay_right_eye_center)
            target_eye_distance = distance(left_eye_center, right_eye_center)
            scale = target_eye_distance / overlay_eye_distance

            # Create transformation matrix
            M = cv2.getRotationMatrix2D(tuple(overlay_midpoint), angle, scale)

            # Calculate separate vertical translation for mouth alignment
            image_height = img.shape[0]
            relative_mouth_y = (mouth_center[1] - target_midpoint[1]) / image_height
            mouth_translation_y = relative_mouth_y * overlay_img.shape[0]

            M[0, 2] += target_midpoint[0] - overlay_midpoint[0]
            M[1, 2] += mouth_translation_y

            # Warp the overlay image
            transformed_overlay = cv2.warpAffine(overlay_img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

            # Blend the images
            if transformed_overlay.shape[2] == 4:  # If the overlay has an alpha channel
                alpha_mask = transformed_overlay[:, :, 3] / 255.0
                alpha_inv = 1.0 - alpha_mask
                for c in range(0, 3):
                    img[:, :, c] = (alpha_mask * transformed_overlay[:, :, c] + alpha_inv * img[:, :, c])
            else:
                # No alpha channel, simple addition
                img = cv2.addWeighted(img, 1, transformed_overlay, 0.5, 0)

        return img


# Compute the angle in degrees between two points
def compute_angle(p1, p2):
    delta_y = p2[1] - p1[1]
    delta_x = p2[0] - p1[0]
    return np.degrees(np.arctan2(delta_y, delta_x))


# Compute the average angle of the face using eyes and mouth corners
def compute_face_angle(left_eye, right_eye, mouth_left, mouth_right):
    eye_angle = compute_angle(left_eye, right_eye)
    mouth_angle = compute_angle(mouth_left, mouth_right)
    # Average the angles to get a more stable face orientation
    average_angle = (eye_angle + mouth_angle) / 2
    return average_angle


# Compute the Euclidean distance between two points
def distance(p1, p2):
    return np.linalg.norm(p1 - p2)


async def draw_mask_on_face(client):
    for overlay_filename in os.listdir(OVERLAYS_FOLDER):
        try:
            overlay_path = os.path.join(OVERLAYS_FOLDER, overlay_filename)

            dframe = cv2.imread(overlay_path)

            image_input = cv2.cvtColor(dframe, cv2.COLOR_BGR2RGB)

            face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=2,
                                                    min_detection_confidence=0.5)
            image_rows, image_cols, _ = dframe.shape
            results = face_mesh.process(cv2.cvtColor(image_input , cv2.COLOR_BGR2RGB))

            ls_single_face=results.multi_face_landmarks[0].landmark
            output_img = None
            for idx in ls_single_face:
                cord = _normalized_to_pixel_coordinates(idx.x,idx.y,image_cols,image_rows)
                output_img = cv2.putText(image_input, '.', cord,cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 2)
            
            _, buffer = cv2.imencode('.png', output_img)
            output_bytes = buffer.tobytes()
            channel = client.get_channel(1297656271092187237)
            await channel.send(file=discord.File(fp=io.BytesIO(output_bytes), filename='output.png'))
        except Exception:
            logging.exception(traceback.format_exc())
