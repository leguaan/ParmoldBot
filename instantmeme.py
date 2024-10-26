import discord
import random
import os
import cv2
import numpy as np
import mediapipe as mp
import io

OVERLAYS_FOLDER = 'data/faces'


async def try_handle_instant_meme(message):
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                async with message.channel.typing():
                    # Download the image
                    img_bytes = await attachment.read()
                    np_arr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

                    # Process the image
                    output_img = await process_image(img)

                    if output_img is None:
                        # Skip message if no face with eyes detected
                        return

                    # Convert output image to bytes
                    _, buffer = cv2.imencode('.png', output_img)
                    output_bytes = buffer.tobytes()

                    await message.channel.send(file=discord.File(fp=io.BytesIO(output_bytes), filename='output.png'))
                    break  # Stop processing other attachments


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
            # Get eye landmarks
            left_eye_indices = [33, 133]
            right_eye_indices = [362, 263]

            left_eye_points = []
            right_eye_points = []

            for idx in left_eye_indices:
                x = face_landmarks.landmark[idx].x * img.shape[1]
                y = face_landmarks.landmark[idx].y * img.shape[0]
                left_eye_points.append((x, y))

            for idx in right_eye_indices:
                x = face_landmarks.landmark[idx].x * img.shape[1]
                y = face_landmarks.landmark[idx].y * img.shape[0]
                right_eye_points.append((x, y))

            # Ensure eye points are detected
            if not left_eye_points or not right_eye_points:
                continue  # Skip if eyes are not detected

            left_eye_center = np.mean(left_eye_points, axis=0)
            right_eye_center = np.mean(right_eye_points, axis=0)
            target_midpoint = (left_eye_center + right_eye_center) / 2

            # Pick a random overlay image
            overlay_filename = random.choice(os.listdir(OVERLAYS_FOLDER))
            overlay_path = os.path.join(OVERLAYS_FOLDER, overlay_filename)
            overlay_img = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)

            flip_vertical = random.choice([True, False])
            if flip_vertical:
                overlay_img = cv2.flip(overlay_img, 1)  # Flip vertically

            # Process overlay image with face mesh
            overlay_results = face_mesh.process(cv2.cvtColor(overlay_img, cv2.COLOR_BGR2RGB))

            if not overlay_results.multi_face_landmarks:
                continue  # Skip if no landmarks are found in overlay

            overlay_face_landmarks = overlay_results.multi_face_landmarks[0]

            # Get eye landmarks in overlay image
            overlay_left_eye_points = []
            overlay_right_eye_points = []

            for idx in left_eye_indices:
                x = overlay_face_landmarks.landmark[idx].x * overlay_img.shape[1]
                y = overlay_face_landmarks.landmark[idx].y * overlay_img.shape[0]
                overlay_left_eye_points.append((x, y))

            for idx in right_eye_indices:
                x = overlay_face_landmarks.landmark[idx].x * overlay_img.shape[1]
                y = overlay_face_landmarks.landmark[idx].y * overlay_img.shape[0]
                overlay_right_eye_points.append((x, y))

            if not overlay_left_eye_points or not overlay_right_eye_points:
                continue  # Skip if overlay eyes are not detected

            overlay_left_eye_center = np.mean(overlay_left_eye_points, axis=0)
            overlay_right_eye_center = np.mean(overlay_right_eye_points, axis=0)
            overlay_midpoint = (overlay_left_eye_center + overlay_right_eye_center) / 2

            # Compute angle and scale for alignment
            def compute_angle(p1, p2):
                delta_y = p2[1] - p1[1]
                delta_x = p2[0] - p1[0]
                return np.degrees(np.arctan2(delta_y, delta_x))

            angle_target = compute_angle(left_eye_center, right_eye_center)
            angle_overlay = compute_angle(overlay_left_eye_center, overlay_right_eye_center)
            angle = angle_target - angle_overlay

            # Compute scale based on distance between eyes
            def distance(p1, p2):
                return np.linalg.norm(p1 - p2)

            overlay_eye_distance = distance(overlay_left_eye_center, overlay_right_eye_center)
            target_eye_distance = distance(left_eye_center, right_eye_center)
            scale = target_eye_distance / overlay_eye_distance

            # Create transformation matrix
            M = cv2.getRotationMatrix2D(tuple(overlay_midpoint), angle, scale)
            M[0, 2] += target_midpoint[0] - overlay_midpoint[0]
            M[1, 2] += target_midpoint[1] - overlay_midpoint[1]

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
