import cmd
import logging
import time

from manager import PhoneManager
from voice_channel import VoiceChannel

class PhoneCLI(cmd.Cmd):
    intro = "Welcome to the ProSLIC CLI. Type help or ? to list commands.\n"
    prompt = "PhoneCLI> "

    def __init__(self, manager: PhoneManager):
        super().__init__()
        self.manager = manager
        self.logger = logging.getLogger("PhoneCLI")

    def _getChannel(self, channel):
        return self.manager.getChannel(channel)

    def do_get_channels(self, arg):
        """Get the number of channels."""
        count = self.manager.getChannelCount()
        print(f"Number of channels: {count}")

    def do_read_hook_status(self, arg):
        """Read the hook status for all channels."""
        for idx in range(self.manager.getChannelCount()):
            status = self._getChannel(idx).getHookState()
            print(f"Channel {idx}: {status.name}")

    def do_start_ring(self, arg):
        """Start ring: start_ring <channel> [caller]"""
        args = arg.split()
        if len(args) < 1:
            print("Usage: start_ring <channel> [caller]")
            return
        try:
            channel = int(args[0])
            caller = args[1] if len(args) > 1 else None
            self._getChannel(channel).startRing(caller)
        except ValueError:
            print("Error: Channel must be an integer.")

    def do_stop_ring(self, arg):
        """Stop ring: stop_ring <channel>"""
        if not arg:
            print("Usage: stop_ring <channel>")
            return
        try:
            channel = int(arg)
            self._getChannel(channel).stopRing()
        except ValueError:
            print("Error: Channel must be an integer.")

    def do_stop_all_rings(self, arg):
        """Stop all rings on all channels."""
        for idx in range(self.manager.getChannelCount()):
            self._getChannel(idx).stopRing()

    def do_test_ringer(self, arg):
        """Test the ringer."""
        print("Ringing each channel:")
        for idx in range(self.manager.getChannelCount()):
            channel = self._getChannel(idx)        
            print(f"Ringing channel: {channel.channel_id}")
            channel.testRing()
            time.sleep(5)
        print("Test completed!")

    def do_set_tone(self, arg):
        """Set tone: set_tone <channel> <tone_type> (dial, ringing, busy)"""
        args = arg.split()
        if len(args) != 2:
            print("Usage: set_tone <channel> <tone_type>")
            return
        try:
            channel = int(args[0])
            tone_type = args[1].lower()
            if tone_type not in ("dial", "ringing", "busy"):
                print("Error: tone_type must be one of (dial, ringing, busy)")
                return
            # self._getChannel(channel).setTone(tone_type)
            print(f"Not implemented yet.")
        except ValueError:
            print("Error: Channel must be an integer.")

    def do_stop_tone(self, arg):
        """Stop tone: stop_tone <channel>"""
        if not arg:
            print("Usage: stop_tone <channel>")
            return
        try:
            channel = int(arg)
            # self._getChannel(channel).stopTone()
            print(f"Not implemented yet.")
        except ValueError:
            print("Error: Channel must be an integer.")

    def do_exit(self, arg):
        """Exit the CLI."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        """Handle Ctrl+D to exit."""
        return self.do_exit()

    def emptyline(self):
        """Do nothing on empty input line."""
        pass