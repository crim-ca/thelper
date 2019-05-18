"""Regression task interface module.

This module contains a class that defines the objectives of models/trainers for regression tasks.
"""
import logging
from typing import Optional  # noqa: F401

import numpy as np

from thelper.tasks.utils import Task

logger = logging.getLogger(__name__)


class Regression(Task):
    """Interface for n-dimension regression tasks.

    This specialization requests that when given an input tensor, the trained model should
    provide an n-dimensional target prediction. This is a fairly generic task that (unlike
    image classification and semantic segmentation) is not linked to a pre-existing set of
    possible solutions. The task interface is used to carry useful metadata for this task,
    e.g. input/output shapes, types, and min/max values for rounding/saturation.

    Attributes:
        input_shape: a numpy-compatible shape to expect model inputs to be in.
        target_shape: a numpy-compatible shape to expect the predictions to be in.
        target_type: a numpy-compatible type to cast the predictions to (if needed).
        target_min: an n-dim tensor containing minimum target values (if applicable).
        target_max: an n-dim tensor containing maximum target values (if applicable).
        input_key: the key used to fetch input tensors from a sample dictionary.
        target_key: the key used to fetch target (groundtruth) values from a sample dictionary.
        meta_keys: the list of extra keys provided by the data parser inside each sample.

    .. seealso::
        | :class:`thelper.tasks.utils.Task`
        | :class:`thelper.train.regr.RegressionTrainer`
        | :class:`thelper.tasks.regr.SuperResolution`
        | :class:`thelper.tasks.detect.Detection`
    """

    def __init__(self, input_key, target_key, meta_keys=None, input_shape=None,
                 target_shape=None, target_type=None, target_min=None, target_max=None):
        """Receives and stores the keys produced by the dataset parser(s)."""
        super(Regression, self).__init__(input_key, target_key, meta_keys)
        self.input_shape = input_shape
        self.target_shape = target_shape
        self.target_type = target_type
        self.target_min = target_min
        self.target_max = target_max
        if self.target_type is not None:
            assert not isinstance(self.target_min, np.ndarray) or self.target_min.dtype == self.target_type, \
                "invalid target min dtype"
            assert not isinstance(self.target_max, np.ndarray) or self.target_max.dtype == self.target_type, \
                "invalid target max dtype"
        if self.target_shape is not None:
            assert not isinstance(self.target_min, np.ndarray) or self.target_min.shape == self.target_shape, \
                "invalid target min shape"
            assert not isinstance(self.target_max, np.ndarray) or self.target_max.shape == self.target_shape, \
                "invalid target max shape"
        if isinstance(self.target_min, np.ndarray) and isinstance(self.target_max, np.ndarray):
            assert self.target_min.shape == self.target_max.shape, "target min/max shape mismatch"

    @property
    def input_shape(self):
        """Returns the shape of the input tensors to be processed by the model."""
        return self._input_shape

    @input_shape.setter
    def input_shape(self, input_shape):
        """Sets the shape of the input tensors to be processed by the model."""
        if input_shape is not None:
            if isinstance(input_shape, list):
                input_shape = tuple(input_shape)
            assert isinstance(input_shape, tuple) and all([isinstance(v, int) for v in input_shape]), \
                "unexpected input shape type (should be tuple of integers)"
        self._input_shape = input_shape

    @property
    def target_shape(self):
        """Returns the shape of the output tensors to be generated by the model."""
        return self._target_shape

    @target_shape.setter
    def target_shape(self, target_shape):
        """Sets the shape of the output tensors to be generated by the model."""
        if target_shape is not None:
            if isinstance(target_shape, list):
                target_shape = tuple(self.target_shape)
            assert isinstance(target_shape, tuple) and all([isinstance(v, int) for v in target_shape]), \
                "unexpected target shape type (should be tuple of integers)"
        self._target_shape = target_shape

    @property
    def target_type(self):
        """Returns the type of the output tensors to be generated by the model."""
        return self._target_type

    @target_type.setter
    def target_type(self, target_type):
        """Sets the type of the output tensors to be generated by the model."""
        if target_type is not None:
            if isinstance(target_type, str):
                import thelper.utils
                target_type = thelper.utils.import_class(target_type)
            assert issubclass(target_type, np.generic), "target type should be a numpy-compatible type"
        self._target_type = target_type

    @property
    def target_min(self):
        """Returns the minimum target value(s) to be generated by the model."""
        return self._target_min

    @target_min.setter
    def target_min(self, target_min):
        """Sets the minimum target value(s) to be generated by the model."""
        if target_min is not None:
            if isinstance(target_min, (list, tuple)):
                target_min = np.asarray(target_min)
            assert isinstance(target_min, np.ndarray), "target_min should be passed as list/tuple/ndarray"
        self._target_min = target_min

    @property
    def target_max(self):
        """Returns the maximum target value(s) to be generated by the model."""
        return self._target_max

    @target_max.setter
    def target_max(self, target_max):
        """Sets the maximum target value(s) to be generated by the model."""
        if target_max is not None:
            if isinstance(target_max, (list, tuple)):
                target_max = np.asarray(target_max)
            assert isinstance(target_max, np.ndarray), "target_max should be passed as list/tuple/ndarray"
        self._target_max = target_max

    def check_compat(self, task, exact=False):
        # type: (Regression, Optional[bool]) -> bool
        """Returns whether the current task is compatible with the provided one or not.

        This is useful for sanity-checking, and to see if the inputs/outputs of two models
        are compatible. If ``exact = True``, all fields will be checked for exact (perfect)
        compatibility (in this case, matching meta keys).
        """
        if isinstance(task, Regression):
            # if both tasks are related to regression: all non-None keys and specs must match
            return (self.input_key == task.input_key and
                    (self.gt_key is None or task.gt_key is None or self.gt_key == task.gt_key) and
                    (self.input_shape is None or task.input_shape is None or self.input_shape == task.input_shape) and
                    (self.target_shape is None or task.target_shape is None or self.target_shape == task.target_shape) and
                    (self.target_type is None or task.target_type is None or self.target_type == task.target_type) and
                    (self.target_min is None or task.target_min is None or self.target_min == task.target_min) and
                    (self.target_max is None or task.target_max is None or self.target_max == task.target_max) and
                    (not exact or (set(self.meta_keys) == set(task.meta_keys) and
                                   self.gt_key == task.gt_key and
                                   self.input_shape == task.input_shape and
                                   self.target_shape == task.target_shape and
                                   self.target_type == task.target_type and
                                   self.target_min == task.target_min and
                                   self.target_max == task.target_max)))
        elif type(task) == Task:
            # if 'task' simply has no gt, compatibility rests on input key only
            return not exact and self.input_key == task.input_key and task.gt_key is None
        return False

    def get_compat(self, task):
        """Returns a task instance compatible with the current task and the given one."""
        # currently not checking for input/target param intersections between similar regression tasks
        assert self.check_compat(task), f"cannot create compatible task between:\n\t{str(self)}\n\t{str(task)}"
        meta_keys = list(set(self.meta_keys + task.meta_keys))
        return Regression(input_key=self.input_key, target_key=self.gt_key, meta_keys=meta_keys,
                          input_shape=self.input_shape if self.input_shape is not None else task.input_shape,
                          target_shape=self.target_shape if self.target_shape is not None else task.target_shape,
                          target_type=self.target_type if self.target_type is not None else task.target_type,
                          target_min=self.target_min if self.target_min is not None else task.target_min,
                          target_max=self.target_max if self.target_max is not None else task.target_max)

    def __repr__(self):
        """Creates a print-friendly representation of a segmentation task."""
        return self.__class__.__module__ + "." + self.__class__.__qualname__ + \
            f"(input_key={self.input_key}, target_key={self.gt_key}, meta_keys={self.meta_keys}, " + \
            f"input_shape={self.input_shape}, target_shape={self.target_shape}, target_type={self.target_type}, " + \
            f"target_min={self.target_min}, target_max={self.target_max})"


class SuperResolution(Regression):
    """Interface for super-resolution tasks.

    This specialization requests that when given an input tensor, the trained model should
    provide an identically-shape target prediction that essentially contains more (or more
    adequate) high-frequency spatial components.

    This specialized regression interface is currently used to help display functions.

    Attributes:
        input_shape: a numpy-compatible shape to expect model inputs/outputs to be in.
        target_type: a numpy-compatible type to cast the predictions to (if needed).
        target_min: an n-dim tensor containing minimum target values (if applicable).
        target_max: an n-dim tensor containing maximum target values (if applicable).
        input_key: the key used to fetch input tensors from a sample dictionary.
        target_key: the key used to fetch target (groundtruth) values from a sample dictionary.
        meta_keys: the list of extra keys provided by the data parser inside each sample.

    .. seealso::
        | :class:`thelper.tasks.utils.Task`
        | :class:`thelper.tasks.regr.Regression`
        | :class:`thelper.train.regr.RegressionTrainer`
    """

    def __init__(self, input_key, target_key, meta_keys=None, input_shape=None, target_type=None,
                 target_min=None, target_max=None):
        """Receives and stores the keys produced by the dataset parser(s)."""
        super(SuperResolution, self).__init__(input_key, target_key, meta_keys,
                                              input_shape=input_shape, target_shape=input_shape,
                                              target_type=target_type, target_min=target_min,
                                              target_max=target_max)
