import discord
import random
import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates
import io
import logging

OVERLAYS_FOLDER = 'data/faces'


async def try_handle_instant_meme(message):
    if message.content.startswith('$ignore'):
        return
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                logging.debug(
                    'try_handle_instant_meme',
                    extra={'message_content': message.content, 'message_id': message.id}
                )
                async with message.channel.typing():
                    try:
                        img = await get_img_from_attachment(attachment)
                        faces = get_faces(img)

                        if not faces.multi_face_landmarks:
                            await message.channel.send("No faces detected in the image!")
                            return

                        if message.content.startswith('$mask'):
                            draw_masks_on_faces(img, faces)
                        elif message.content.startswith('$eyes'):
                            draw_specific_points_on_faces(img, faces)
                        elif message.content.startswith('$explainmin'):
                            draw_letters_on_faces(img, faces, '')
                        elif message.content.startswith('$explainfull'):
                            draw_letters_on_faces(img, faces)
                        else:
                            draw_overlays_on_faces(img, faces)

                        await send_img_to_channel(img, message.channel)
                    except Exception as e:
                        logging.error(f"Error processing image: {str(e)}")
                        await message.channel.send("Failed to process image. Please try another.")


def draw_overlays_on_faces(img, faces):
    points_on_faces = get_specific_points_on_faces(img, faces)
    if not points_on_faces:
        return img

    for face in points_on_faces:
        if None in face or len(face) < 2:
            continue

        try:
            # 1. Overlay loading with validation
            overlay = get_img_from_path(os.path.join(
                OVERLAYS_FOLDER,
                random.choice([f for f in os.listdir(OVERLAYS_FOLDER)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            ))
            if overlay is None:
                continue

            # 2. Transform and orient overlay
            overlay = transform_overlay(img, overlay)
            best_overlay = choose_best_overlay_simple(overlay, face)
            if best_overlay.size == 0:
                continue

            # 3. Calculate transformation matrix
            overlay_points = get_specific_points_on_faces(
                best_overlay,
                get_faces(best_overlay, no_of_faces=1)
            )
            if not overlay_points or None in overlay_points[0]:
                continue

            # Extract source and target points
            p1_src, p2_src = np.array(overlay_points[0][:2])
            p1_dst, p2_dst = np.array(face[:2])

            # Build transformation matrix
            A = np.array([
                [p1_src[0], -p1_src[1], 1, 0],
                [p1_src[1], p1_src[0], 0, 1],
                [p2_src[0], -p2_src[1], 1, 0],
                [p2_src[1], p2_src[0], 0, 1]
            ])
            b = np.array([p1_dst[0], p1_dst[1], p2_dst[0], p2_dst[1]])
            a, b_param, tx, ty = np.linalg.lstsq(A, b, rcond=None)[0]

            # 4. Apply transformation with bounds checking
            rows, cols = img.shape[:2]
            M = np.array([[a, -b_param, tx], [b_param, a, ty]])

            # Calculate valid region
            h, w = best_overlay.shape[:2]
            pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1]], dtype=np.float32)
            warped_pts = cv2.transform(pts.reshape(1, -1, 2), M).reshape(-1, 2)

            # Create mask for visible area
            mask = np.zeros((rows, cols), dtype=np.uint8)
            cv2.fillConvexPoly(mask, np.clip(warped_pts, 0, [cols - 1, rows - 1]).astype(int), 1)

            # Warp overlay with transparency
            transformed = cv2.warpAffine(
                best_overlay, M, (cols, rows),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_TRANSPARENT
            )

            # 5. Alpha blending with mask
            alpha = (transformed[..., 3] / 255.0 if transformed.shape[2] == 4
                     else np.ones(transformed.shape[:2], dtype=np.float32))
            alpha = alpha * (mask / 255.0)  # Combine masks

            # Final blending with broadcasting
            img = (
                    alpha[..., np.newaxis] * transformed[..., :3] +
                    (1 - alpha[..., np.newaxis]) * img
            ).astype(np.uint8)

        except Exception as e:
            logging.error(f"Overlay error: {str(e)}")
            continue

    return img


def get_img_from_path(path):
    overlay = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if overlay is None:
        print(f"Failed to load overlay: {path}")
        return None

    # Preserve existing alpha channel
    if overlay.ndim == 2:  # Grayscale
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGRA)
    elif overlay.shape[2] == 3:  # BGR
        overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2BGRA)

    print(f"Loaded overlay: {path} | Shape: {overlay.shape} | Channels: {overlay.shape[2]}")
    return overlay


def choose_best_overlay_simple(overlay, src_eye_points):
    if overlay is None or len(src_eye_points) < 2:
        return overlay

    # Simplified geometric flip detection
    left_eye_x = src_eye_points[0][0]
    right_eye_x = src_eye_points[1][0]
    return cv2.flip(overlay, 1) if left_eye_x > right_eye_x else overlay


async def get_img_from_attachment(attachment):
    img_bytes = await attachment.read()
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

    # Handle different image formats properly
    if img is None:
        return None

    # Convert to 3-channel BGR with alpha removal
    if img.ndim == 2:  # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:  # Always assume BGRA for OpenCV
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif img.shape[2] == 3:  # Ensure BGR format
        pass  # Already in correct format

    return img


def get_faces(img, no_of_faces=10):
    if img.ndim == 2:
        processing_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        processing_img = img.copy()

    with mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=no_of_faces,
            refine_landmarks=True,
            min_detection_confidence=0.5
    ) as face_mesh:
        rgb_img = cv2.cvtColor(processing_img, cv2.COLOR_BGR2RGB)
        return face_mesh.process(rgb_img)


def get_specific_points_on_faces(img, faces, points=[33, 263]):
    points_on_faces = []
    image_rows, image_cols, _ = img.shape
    if faces.multi_face_landmarks:
        for face in faces.multi_face_landmarks:
            face_points = []
            for idx in points:
                landmark = face.landmark[idx]
                cord = _normalized_to_pixel_coordinates(
                    landmark.x, landmark.y, image_cols, image_rows
                )
                if cord is None:
                    break  # Skip incomplete faces
                face_points.append(cord)
            if len(face_points) == len(points):
                points_on_faces.append(face_points)
    return points_on_faces


def draw_masks_on_faces(img, faces):
    image_rows, image_cols, _ = img.shape
    if not faces.multi_face_landmarks:
        return

    for face in faces.multi_face_landmarks:
        for landmark in face.landmark:
            cord = _normalized_to_pixel_coordinates(
                landmark.x, landmark.y, image_cols, image_rows
            )
            if cord:  # Only draw valid coordinates
                cv2.putText(img, '.', cord, cv2.FONT_HERSHEY_SIMPLEX,
                            0.3, (0, 0, 255), 2)


def draw_specific_points_on_faces(img, faces, points=[33, 263]):
    image_rows, image_cols, _ = img.shape
    if not faces.multi_face_landmarks:
        return

    for face in faces.multi_face_landmarks:
        for idx in points:
            if idx >= len(face.landmark):
                continue  # Skip invalid indices
            landmark = face.landmark[idx]
            cord = _normalized_to_pixel_coordinates(
                landmark.x, landmark.y, image_cols, image_rows
            )
            if cord:
                cv2.putText(img, '.', cord, cv2.FONT_HERSHEY_SIMPLEX,
                            0.3, (0, 0, 255), 2)


def draw_letters_on_faces(img, faces, alt='.'):
    image_rows, image_cols, _ = img.shape
    letters = {
        33: 'l', 159: 't', 133: 'r', 145: 'b',
        362: 'L', 386: 'T', 263: 'R', 374: 'B',
        61: 'm', 409: 'M'
    }

    if not faces.multi_face_landmarks:
        return

    for face in faces.multi_face_landmarks:
        for i, landmark in enumerate(face.landmark):
            if i not in letters and alt == '':
                continue

            cord = _normalized_to_pixel_coordinates(
                landmark.x, landmark.y, image_cols, image_rows
            )
            if cord:
                text = letters.get(i, alt)
                cv2.putText(img, text, cord, cv2.FONT_HERSHEY_SIMPLEX,
                            0.3, (0, 0, 255), 2)


async def send_img_to_channel(img, channel):
    if img is None or img.size == 0:
        logging.error("Tried to send empty image")
        return

    try:
        _, buffer = cv2.imencode('.png', img)
        if buffer is None:
            raise ValueError("Image encoding failed")

        await channel.send(file=discord.File(
            fp=io.BytesIO(buffer.tobytes()),
            filename='output.png'
        ))
    except Exception as e:
        logging.error(f"Failed to send image: {str(e)}")
        await channel.send("Failed to process image output")


def calculate_average_brightness(image):
    if image is None or image.size == 0:
        return 0.0
    return np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))


def calculate_average_contrast(image):
    if image is None or image.size == 0:
        return 0.0
    return np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))


def transform_overlay(image, overlay_image):
    if image is None or overlay_image is None:
        return overlay_image

    try:
        if overlay_image.ndim == 2:
            overlay_image = cv2.cvtColor(overlay_image, cv2.COLOR_GRAY2BGRA)

        source_brightness = calculate_average_brightness(image)
        source_contrast = calculate_average_contrast(image)
        overlay_brightness = calculate_average_brightness(overlay_image)
        overlay_contrast = calculate_average_contrast(overlay_image)

        contrast_factor = source_contrast / (overlay_contrast + 1e-6)
        brightness_adjustment = source_brightness - overlay_brightness * contrast_factor

        if overlay_image.shape[2] == 4:
            b, g, r, alpha = cv2.split(overlay_image)
            overlay_rgb = cv2.merge((b, g, r))
            transformed_rgb = cv2.convertScaleAbs(
                overlay_rgb, alpha=contrast_factor, beta=brightness_adjustment
            )
            return cv2.merge((transformed_rgb, alpha))
        else:
            return cv2.convertScaleAbs(
                overlay_image, alpha=contrast_factor, beta=brightness_adjustment
            )
    except Exception as e:
        logging.error(f"Overlay transform failed: {str(e)}")
        return overlay_image
