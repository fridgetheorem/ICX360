"""
Base class for MExGen explainers.

The MExGen framework is described in:
    Multi-Level Explanations for Generative Language Models.
    Lucas Monteiro Paes and Dennis Wei et al.
    The 63rd Annual Meeting of the Association for Computational Linguistics (ACL 2025).
    https://arxiv.org/abs/2403.14459
"""
# Assisted by watsonx Code Assistant in formatting and augmenting docstrings.

from icx360.algorithms.lbbe import LocalBBExplainer
from icx360.utils.scalarizers import ProbScalarizedModel, TextScalarizedModel
from icx360.utils.segmenters import SpaCySegmenter, exclude_non_alphanumeric


class MExGenExplainer(LocalBBExplainer):
    """
    Base class for MExGen explainers.

    Attributes:
        model (icx360.utils.model_wrappers.Model):
            Model to explain, wrapped in an icx360.utils.model_wrappers.Model object.
        segmenter (icx360.utils.segmenters.SpaCySegmenter):
            Object for segmenting input text into units using a spaCy model.
        scalarized_model (icx360.utils.scalarizers.Scalarizer):
            "Scalarized model" that further wraps `model` with a method for computing scalar values
            based on the model's inputs or outputs.
    """
    def __init__(self, model, segmenter="en_core_web_trf", scalarizer="prob", **kwargs):
        """
        Initialize MExGen explainer.

        Args:
            model (icx360.utils.model_wrappers.Model):
                Model to explain, wrapped in an icx360.utils.model_wrappers.Model object.
            segmenter (str):
                Name of spaCy model to use in segmenter (icx360.utils.segmenters.SpaCySegmenter).
            scalarizer (str):
                Type of scalarizer to use.
                    "prob": probability of generating original output conditioned on perturbed inputs
                        (instantiates an icx360.utils.scalarizers.ProbScalarizedModel).
                    "text": similarity scores between original output and perturbed outputs
                        (instantiates an icx360.utils.scalarizers.TextScalarizedModel).
            **kwargs (dict):
                Additional keyword arguments for initializing scalarizer.

        Raises:
            ValueError: If `scalarizer` is not "prob" or "text".
        """
        self.model = model

        # Instantiate segmenter
        self.segmenter = SpaCySegmenter(segmenter)

        # Instantiate scalarized model
        if scalarizer == "prob":
            self.scalarized_model = ProbScalarizedModel(model)
        elif scalarizer == "text":
            self.scalarized_model = TextScalarizedModel(model, **kwargs)
        else:
            raise ValueError("Scalarizer not supported")

    def segment_input(self, input_orig, unit_types="p", ind_segment=True, segment_type="s", max_phrase_length=10):
        """
        Segment input text (if needed).

        Args:
            input_orig (str or List[str]):
                Input text as a single unit (if str) or segmented sequence of units (List[str]).
            unit_types (str or List[str]):
                Types of units in input_orig.
                    "p" for paragraph, "s" for sentence, "w" for word,
                    "n" for not to be perturbed/attributed to.
                If str, applies to all units in input_orig, otherwise unit-specific.
            ind_segment (bool or List[bool]):
                Whether to segment input text.
                If bool, applies to all units; if List[bool], applies to each unit individually.
            segment_type (str):
                Type of units to segment into: "s" for sentences, "w" for words, "ph" for phrases.
            max_phrase_length (int):
                Maximum phrase length in terms of spaCy tokens (default 10).

        Returns:
            input_orig (List[str]):
                Segmented input text.
            unit_types (List[str]):
                Updated types of units.
        """
        # Convert ind_segment to list if needed
        if type(ind_segment) is bool:
            ind_segment = [ind_segment]
        # Segment input text if needed
        if type(input_orig) is str or any(ind_segment):
            # Call segmenter
            input_orig, unit_types, _ = self.segmenter.segment_units(input_orig, ind_segment, unit_types,
                                                                     segment_type=segment_type,
                                                                     max_phrase_length=max_phrase_length)
            # Exclude units without alphanumeric characters from perturbation
            unit_types = exclude_non_alphanumeric(unit_types, input_orig)
        num_units = len(input_orig)

        # Expand to list if needed
        if type(unit_types) is str:
            unit_types = [unit_types] * num_units

        return input_orig, unit_types
