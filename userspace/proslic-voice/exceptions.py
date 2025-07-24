class DeviceError(Exception):
    def __init__(self, device, message):
        super().__init__(f"{message} (Device: {device.NAME})")
        self.device_name = device.NAME
        self.message = message

class InitializationError(DeviceError):
    def __init__(self, device):
        super().__init__(device, "Failed to initialize")

class TimeoutError(DeviceError):
    def __init__(self, device):
        super().__init__(device, f"Timout occurred while performing an operation")

class CommunicationError(DeviceError):
    def __init__(self, device):
        super().__init__(device, "Failed to communicate")

class BlobInvalidError(DeviceError):
    def __init__(self, device, blob_version):
        super().__init__(device, f"Provided blob with id {hex(blob_version)} is invalid")

class BlobUploadError(DeviceError):
    def __init__(self, device, blob_version):
        super().__init__(device, f"Failed to upload blob with id {hex(blob_version)}")

class BlobVerifyError(DeviceError):
    def __init__(self, device, blob_version):
        super().__init__(device, f"Failed to verify blob with id {hex(blob_version)}")

class InvalidCalibrationError(DeviceError):
    def __init__(self, device):
        super().__init__(device, f"Invalid calibration parameters or unexpected result")

class ChannelError(Exception):
    def __init__(self, channel, message):
        super().__init__(f"{message} (Channel: {channel.getChannelId()})")
        self.channel_id = channel.getChannelId()
        self.message = message

class RingUnhookException(Exception):
    def __init__(self, channel):
        super().__init__(channel, f"Hadset is UNHOOKED")

class PlaybackError(Exception):
    """Raised when playback fails"""
    pass