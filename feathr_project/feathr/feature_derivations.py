from __future__ import annotations
from typing import List, Optional

from copy import copy, deepcopy
from jinja2 import Template
from typing import Union
from feathr.dtype import FeatureType, ValueType
from feathr.feature import Feature
from feathr.typed_key import DUMMY_KEY, TypedKey
from feathr.transformation import ExpressionTransformation, RowTransformation

class DerivedFeature:
    """A derived feature is a feature defined on top of other features, rather than external data source.
    Attributes:
        name: derived feature name
        feature_type: type of derived feature
        key: join key of the derived feature
        input_features: features that this derived features depends on
        transform: transformation that produces the derived feature value, based on the input_features
        feature_alias: Rename the derived feature to `feature_alias`. Default to None.
        key_alias: Rename the key of derived feature to `key`. Default to None.
    """

    def __init__(self,
                name: str,
                feature_type: FeatureType,
                input_features: Union[DerivedFeature, Feature, List[Union[DerivedFeature, Feature]]],
                transform: Union[str, RowTransformation],
                key: Optional[Union[TypedKey, List[TypedKey]]] = [DUMMY_KEY],
                feature_alias:Optional[str] = None,
                key_alias: Optional[List[str]] = None) -> None:
        self.name = name
        self.feature_type = feature_type
        self.key = key if isinstance(key, List) else [key]
        self.input_features = input_features if isinstance(input_features, List) else [input_features]
        self.transform = transform if isinstance(transform, RowTransformation) else ExpressionTransformation(transform) 
        self.feature_alias = feature_alias if feature_alias else name
        self.key_alias = self.get_key_alias(key_alias)

    def get_key_alias(self, key_alias: Optional[List[str]] = None):
        default_key_alias = [k.key_column_alias for k in self.key]
        return key_alias if key_alias else default_key_alias

    def with_key(self, alias: List[str]) -> DerivedFeature:
        assert(len(alias) == len(self.key))
        new_key = []
        for i in range(0, len(alias)):
            typed_key = deepcopy(self.key[i])
            typed_key.key_column_alias=alias[i]
            new_key.append(typed_key)

        res = deepcopy(self)
        res.key=new_key
        res.key_alias=alias
        return res

    def as_feature(self, feature_alias: str) -> DerivedFeature:
        new_feature = deepcopy(self)
        new_feature.feature_alias=feature_alias
        return new_feature

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result


    def to_feature_config(self) -> str:
        tm = Template("""
            {{derived_feature.name}}: {
                key: [{{','.join(derived_feature.key_alias)}}]
                inputs: {
                    {% for feature in derived_feature.input_features %}
                        {{feature.feature_alias}}: {
                            key: [{{','.join(feature.key_alias)}}],
                            feature: {{feature.name}}
                        }
                    {% endfor %}
                }
                definition: {{derived_feature.transform.to_feature_config()}}
                {{derived_feature.feature_type.to_feature_config()}}
            }
        """)
        return tm.render(derived_feature=self)
