"""Precontroller module.

Responsible for triggering scene linkages based on prediction results,
supporting scene template configuration and conflict resolution.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SceneTemplate:
    """Scene template.

    Defines the trigger conditions and control commands for a single scene.

    Attributes:
        scene_id: Scene ID.
        name: Scene name.
        description: Scene description.
        trigger_conditions: List of trigger conditions.
        actions: List of control commands.
        priority: Priority (higher value = higher priority).
        cooldown: Cooldown time (seconds).
        last_triggered: Timestamp of the last trigger.
    """

    def __init__(
        self,
        scene_id: str,
        name: str,
        description: str,
        trigger_conditions: Dict,
        actions: Dict,
        priority: int = 0,
        cooldown: int = 60
    ):
        """Initialize the scene template.

        Args:
            scene_id: Scene ID.
            name: Scene name.
            description: Scene description.
            trigger_conditions: Trigger condition dictionary, e.g.:
                {
                    "prediction_min": 0.7,
                    "temperature_max": 28.0,
                    "brightness_max": 100.0
                }
            actions: Control command dictionary, e.g.:
                {
                    "Light_TH": 1,
                    "Light_CU": 0
                }
            priority: Priority.
            cooldown: Cooldown time (seconds).
        """
        self.scene_id = scene_id
        self.name = name
        self.description = description
        self.trigger_conditions = trigger_conditions
        self.actions = actions
        self.priority = priority
        self.cooldown = cooldown
        self.last_triggered: Optional[float] = None

    def should_trigger(
        self,
        prediction_result: float,
        context: Dict
    ) -> bool:
        """Determine whether the scene should be triggered.

        Args:
            prediction_result: Prediction probability.
            context: Current environmental context (temperature, light, etc.).

        Returns:
            True if should trigger, False otherwise.
        """
        # Check cooldown
        if self.last_triggered is not None:
            time_since_last = time.time() - self.last_triggered
            if time_since_last < self.cooldown:
                logger.debug(
                    "Scene '%s' is cooling down, %.1f seconds remaining",
                    self.name,
                    self.cooldown - time_since_last
                )
                return False

        # Check trigger conditions
        # Prediction probability conditions
        if "prediction_min" in self.trigger_conditions:
            if prediction_result < self.trigger_conditions["prediction_min"]:
                return False
        if "prediction_max" in self.trigger_conditions:
            if prediction_result > self.trigger_conditions["prediction_max"]:
                return False

        # Environmental conditions
        for key, condition in self.trigger_conditions.items():
            if key.startswith("prediction_"):
                continue

            if key not in context:
                logger.warning("Context missing field: %s", key)
                continue

            value = context[key]

            # Check minimum condition
            min_key = f"{key}_min"
            if min_key in self.trigger_conditions:
                if value < self.trigger_conditions[min_key]:
                    return False

            # Check maximum condition
            max_key = f"{key}_max"
            if max_key in self.trigger_conditions:
                if value > self.trigger_conditions[max_key]:
                    return False

        return True

    def trigger(self) -> Dict:
        """Trigger the scene.

        Returns:
            Control command dictionary.
        """
        self.last_triggered = time.time()
        logger.info("Scene '%s' triggered (ID: %s)", self.name, self.scene_id)
        return self.actions.copy()

    def to_dict(self) -> Dict:
        """Convert to dictionary format.

        Returns:
            Dictionary representation of the scene template.
        """
        return {
            "scene_id": self.scene_id,
            "name": self.name,
            "description": self.description,
            "trigger_conditions": self.trigger_conditions,
            "actions": self.actions,
            "priority": self.priority,
            "cooldown": self.cooldown,
        }


class Precontroller:
    """Precontroller.

    Triggers scene linkages based on prediction results,
    supporting multi-scene priority and conflict resolution.

    Attributes:
        scene_templates: List of scene templates.
        scene_config_path: Path to the scene configuration file.
    """

    def __init__(self, scene_config_path: Optional[str] = None):
        """Initialize the precontroller.

        Args:
            scene_config_path: Path to the scene configuration file (JSON format).
        """
        self.scene_templates: List[SceneTemplate] = []

        if scene_config_path:
            self.load_scenes(scene_config_path)
        else:
            # Load default scene configuration
            self._load_default_scenes()

        logger.info("Precontroller initialized with %d scene templates", len(self.scene_templates))

    def load_scenes(self, config_path: str) -> None:
        """Load scene configuration from a JSON file.

        Args:
            config_path: Path to the configuration file.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            scenes = config.get("scenes", [])
            for scene_data in scenes:
                scene = SceneTemplate(
                    scene_id=scene_data["scene_id"],
                    name=scene_data["name"],
                    description=scene_data.get("description", ""),
                    trigger_conditions=scene_data["trigger_conditions"],
                    actions=scene_data["actions"],
                    priority=scene_data.get("priority", 0),
                    cooldown=scene_data.get("cooldown", 60)
                )
                self.scene_templates.append(scene)

            # Sort by priority
            self.scene_templates.sort(key=lambda s: s.priority, reverse=True)

            logger.info("Loaded %d scene configurations from %s", len(scenes), config_path)

        except Exception as error:
            logger.error("Failed to load scene configuration: %s", error)
            logger.info("Using default scene configuration")
            self._load_default_scenes()

    def _load_default_scenes(self) -> None:
        """Load default scene configuration."""
        # Scene 1: Automatically turn on AC when temperature is high
        self.scene_templates.append(
            SceneTemplate(
                scene_id="auto_ac_on",
                name="Auto Turn On AC",
                description="Automatically turn on the AC when prediction > 0.7 and temperature > 28°C",
                trigger_conditions={
                    "prediction_min": 0.7,
                    "Temperature_max": 28.0,
                },
                actions={"Light_TH": 1},
                priority=10,
                cooldown=300
            )
        )

        # Scene 2: Automatically turn off AC when temperature is comfortable
        self.scene_templates.append(
            SceneTemplate(
                scene_id="auto_ac_off",
                name="Auto Turn Off AC",
                description="Automatically turn off the AC when prediction < 0.3 and temperature < 25°C",
                trigger_conditions={
                    "prediction_max": 0.3,
                    "Temperature_max": 25.0,
                },
                actions={"Light_TH": 0},
                priority=5,
                cooldown=300
            )
        )

        # Scene 3: Automatically turn on lights and close curtains when light is low
        self.scene_templates.append(
            SceneTemplate(
                scene_id="auto_light_on",
                name="Auto Lights On Curtains Closed",
                description="Automatically turn on lights and close curtains when prediction > 0.6 and brightness < 100",
                trigger_conditions={
                    "prediction_min": 0.6,
                    "Brightness_max": 100.0,
                },
                actions={"Light_CU": 1, "Curtain_status": 0},
                priority=8,
                cooldown=180
            )
        )

        # Scene 4: Automatically turn off lights and open curtains when light is sufficient
        self.scene_templates.append(
            SceneTemplate(
                scene_id="auto_light_off",
                name="Auto Lights Off Curtains Open",
                description="Automatically turn off lights and open curtains when prediction < 0.4 and brightness > 200",
                trigger_conditions={
                    "prediction_max": 0.4,
                    "Brightness_min": 200.0,
                },
                actions={"Light_CU": 0, "Curtain_status": 1},
                priority=6,
                cooldown=180
            )
        )

        # Sort by priority
        self.scene_templates.sort(key=lambda s: s.priority, reverse=True)

        logger.info("Loaded default scene configuration: %d scenes", len(self.scene_templates))

    def evaluate(
        self,
        prediction_result: float,
        context: Dict
    ) -> Dict:
        """Evaluate prediction results and generate control commands.

        Args:
            prediction_result: Prediction probability (between 0 and 1).
            context: Current environmental context, including temperature, light, humidity, etc.

        Returns:
            Device control command dictionary.
        """
        logger.debug(
            "Evaluating prediction result: %.4f, context: %s",
            prediction_result,
            context
        )

        # Find all triggerable scenes
        triggered_scenes = []
        for scene in self.scene_templates:
            if scene.should_trigger(prediction_result, context):
                triggered_scenes.append(scene)

        # If no scene is triggered, return empty dictionary
        if not triggered_scenes:
            logger.debug("No scene triggered")
            return {}

        # Select the scene with highest priority (already sorted by priority)
        selected_scene = triggered_scenes[0]
        control_commands = selected_scene.trigger()

        logger.info(
            "Triggered scene: %s (priority=%d)",
            selected_scene.name,
            selected_scene.priority
        )

        return control_commands

    def evaluate_batch(
        self,
        prediction_results: np.ndarray,
        context: Dict
    ) -> List[Dict]:
        """Batch evaluate prediction results.

        Args:
            prediction_results: Array of prediction probabilities.
            context: Current environmental context.

        Returns:
            List of control commands.
        """
        commands_list = []
        for pred in prediction_results:
            commands = self.evaluate(float(pred), context)
            commands_list.append(commands)

        return commands_list

    def add_scene(self, scene: SceneTemplate) -> None:
        """Add a scene template.

        Args:
            scene: Scene template instance.
        """
        self.scene_templates.append(scene)
        # Re-sort
        self.scene_templates.sort(key=lambda s: s.priority, reverse=True)
        logger.info("Added scene: %s (priority=%d)", scene.name, scene.priority)

    def remove_scene(self, scene_id: str) -> bool:
        """Remove a scene template.

        Args:
            scene_id: Scene ID.

        Returns:
            True if removed successfully, False if not found.
        """
        for i, scene in enumerate(self.scene_templates):
            if scene.scene_id == scene_id:
                removed_scene = self.scene_templates.pop(i)
                logger.info("Removed scene: %s", removed_scene.name)
                return True

        logger.warning("Scene ID not found: %s", scene_id)
        return False

    def get_scene(self, scene_id: str) -> Optional[SceneTemplate]:
        """Get a specific scene template.

        Args:
            scene_id: Scene ID.

        Returns:
            Scene template instance, or None if not found.
        """
        for scene in self.scene_templates:
            if scene.scene_id == scene_id:
                return scene
        return None

    def list_scenes(self) -> List[Dict]:
        """List all scene templates.

        Returns:
            List of scene template dictionaries.
        """
        return [scene.to_dict() for scene in self.scene_templates]

    def save_scenes(self, output_path: str) -> bool:
        """Save scene configuration to a JSON file.

        Args:
            output_path: Output file path.

        Returns:
            True if saved successfully, False if failed.
        """
        try:
            config = {
                "scenes": [scene.to_dict() for scene in self.scene_templates]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info("Scene configuration saved to: %s", output_path)
            return True

        except Exception as error:
            logger.error("Failed to save scene configuration: %s", error)
            return False
