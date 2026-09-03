from village.custom_classes.training_protocol_base import TrainingProtocolBase


class TrainingProtocol(TrainingProtocolBase):
    """
    This class defines the training protocol for animal behavior experiments.
    The training protocol is run every time a task is finished and it determines:
    1. Which new task is scheduled for the subject
    2. How training variables change based on performance metrics

    Required methods to implement:
    - __init__: Initialize the training protocol
    - default_training_settings: Define initial parameters. It is called when creating a new subject.
    - update_training_settings: Update parameters after each session.

    Optional method:
    - gui_tabs: Organize the variables in custom GUI tabs
    """


    def __init__(self) -> None:
        """Initialize the training protocol."""
        super().__init__()


    def default_training_settings(self) -> None:
        """
        Define all initial training parameters for new subjects.

        This method is called when creating a new subject, and these parameters
        are saved as the initial values for that subject.

        Required parameters:
        - next_task (str): Name of the next task to run
        - refractory_period (int): Waiting time in seconds between sessions
        - minimum_duration (int): Minimum time in seconds for the task before door2 opens
        - maximum_duration (int): Maximum time in seconds before task stops automatically

        Additional parameters:
        You can define any additional parameters needed for your specific tasks.
        These can be modified between sessions based on subject performance.
        """

        # Required parameters for any training protocol
        self.settings.next_task = "Sound_Localization"  # Next task to run
        self.settings.refractory_period = 3600 * 4  # 4 hours between sessions of the same subject
        self.settings.minimum_duration = 1  # Minimum duration of 1 second
        self.settings.maximum_duration = 90*60  # Maximum duration of 90 minutes

        ## Task-specific parameters

        # sound parameters
        self.settings.sound_duration = 0.05 #50ms

        # time to wait after sound is played before starting a new trial
        self.settings.time_to_wait_after_sound = 2  # seconds


    def update_training_settings(self) -> None:
        pass


    def define_gui_tabs(self):
        pass