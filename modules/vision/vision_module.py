# modules/vision.py

import cv2
import mediapipe as mp
import numpy as np
import threading
import face_recognition
from ultralytics import YOLO
import torch

class VisionModule:
    def __init__(self, config, logger, event_bus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus
        self.cap = None
        self.running = False
        self.processing_thread = None
        
        # Initialize MediaPipe solutions
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=4,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_hands = mp.solutions.hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize YOLO
        self.yolo_model = YOLO('yolov8n.pt')  # Using nano model for better performance
        
        # Face recognition
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.process_this_frame = True
        
        # Device optimization for M1
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")

    def start(self):
        """Start the vision module in a separate thread"""
        if not self.running:
            self.running = True
            self.initialize()
            self.processing_thread = threading.Thread(target=self.process_loop)
            self.processing_thread.start()
    
    def process_loop(self):
        """Main processing loop for vision module"""
        while self.running:
            self.process()

    def initialize(self):
        """Initialize video capture and models"""
        try:
            self.cap = cv2.VideoCapture(self.config.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Move YOLO model to appropriate device
            self.yolo_model.to(self.device)
            
            self.logger.info("Vision module initialized successfully")
        except Exception as e:
            self.logger.error(f"Vision initialization error: {e}")
            raise

    def process(self):
        """Capture and process video frames"""
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe and face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process face mesh
        face_results = self.mp_face_mesh.process(rgb_frame)
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, 
                    face_landmarks,
                    mp.solutions.face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style()
                )
        
        # Process hands
        hand_results = self.mp_hands.process(rgb_frame)
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp.solutions.hands.HAND_CONNECTIONS
                )
        
        # Face recognition (every other frame)
        if self.process_this_frame:
            # Reduce frame size for faster processing
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
            
            # Find faces
            self.face_locations = face_recognition.face_locations(small_frame)
            self.face_encodings = face_recognition.face_encodings(small_frame, self.face_locations)
            
            # Match faces
            for face_encoding in self.face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]
                
                # Scale back face locations
                for (top, right, bottom, left) in self.face_locations:
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Draw face box and name
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        self.process_this_frame = not self.process_this_frame
        
        # YOLO object detection
        results = self.yolo_model(frame)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Get class name and confidence
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = result.names[cls]
                
                if conf > 0.5:  # Confidence threshold
                    # Draw box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # Emit events for detected objects and faces
        self._emit_detection_events(results)
        
        # Display the frame
        cv2.imshow("Assistant Vision", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.logger.info("Quit command received in Vision module")
            self.stop()

    def _emit_detection_events(self, yolo_results):
        """Emit events for detected objects and faces"""
        detections = {
            'objects': [],
            'faces': [],
            'hands': []
        }
        
        # YOLO detections
        for result in yolo_results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = result.names[cls]
                if conf > 0.5:
                    detections['objects'].append({
                        'class': name,
                        'confidence': conf,
                        'box': box.xyxy[0].tolist()
                    })
        
        # Face detections
        for i, face_encoding in enumerate(self.face_encodings):
            name = "Unknown"
            if len(self.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if True in matches:
                    name = self.known_face_names[matches.index(True)]
            
            detections['faces'].append({
                'name': name,
                'location': self.face_locations[i]
            })
        
        # Emit detection event
        self.event_bus.emit('vision_detections', detections)

    def add_known_face(self, face_image, name):
        """Add a known face to the recognition system"""
        encoding = face_recognition.face_encodings(face_image)[0]
        self.known_face_encodings.append(encoding)
        self.known_face_names.append(name)
        self.logger.info(f"Added face recognition profile for: {name}")

    def stop(self):
        """Stop the vision module"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        self.cleanup()

    def cleanup(self):
        """Release resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.mp_face_mesh.close()
        self.mp_hands.close()
        self.logger.info("Vision module cleaned up")