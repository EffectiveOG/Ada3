# modules/vision.py

import cv2

class VisionModule:
    def __init__(self, config, logger, event_bus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus
        self.cap = None
        self.running = False

    def start(self):
        """Start the vision module"""
        if not self.running:
            self.running = True
            self.initialize()
            self.process_loop()
    
    def process_loop(self):
        """Main processing loop for vision module"""
        while self.running:
            self.process()

    def initialize(self):
        """Initialize video capture"""
        try:
            self.cap = cv2.VideoCapture(self.config.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            self.logger.info("Vision module initialized")
        except Exception as e:
            self.logger.error(f"Vision initialization error: {e}")
    def process(self):
        """Capture and process video frames"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Flip the frame vertically
                frame = cv2.flip(frame, 1)
                
                # Add vision processing logic here
                cv2.imshow("Assistant Vision", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.logger.info("Quit command received in Vision module")
                    self.stop()

    def stop(self):
        """Stop the vision module"""
        self.running = False
        self.cleanup()

    def cleanup(self):
        """Release video capture and close windows."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.logger.info("Vision module cleaned up.")