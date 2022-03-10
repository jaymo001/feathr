from __future__ import annotations
from typing import Dict, Optional, List, Union
from feathr.dtype import ValueType, FeatureType
from feathr.transformation import RowTransformation
from feathr.transformation import ExpressionTransformation
from feathr.typed_key import DUMMY_KEY, TypedKey

from copy import copy, deepcopy
from jinja2 import Template



class Feature:
    """A feature is an individual measurable property or characteristic of an entity.
    It has a feature name, feature type, and a convenient row transformation used to produce its feature value.
    Attributes:
        name: Unique name of the feature. Only alphabet, numbers, and '_' are allowed in the name.
                It can not start with numbers. Note that '.' is NOT ALLOWED!
        feature_type: the feature value type. e.g. INT32, FLOAT, etc.
        entity: The entity that this feature describes. e.g. user.
        transform: A row transformation used to produce its feature value. e.g. amount * 10
        feature_alias: variable name, transformation can reference this feature by the feature_alias. Default to its feature name.
        entity_alias: An alias for the entity in this feature. Default to its entity alias. Useful in complex relation features.
    """
    def __init__(self,
                name: str,
                feature_type: FeatureType,
                key: Optional[Union[TypedKey, List[TypedKey]]] = [DUMMY_KEY],
                transform: Optional[Union[str, RowTransformation]] = None,
                feature_alias: Optional[str] = None,
                key_alias: Optional[List[str]] = None):
        self.name = name
        self.feature_type = feature_type
        self.key = key if isinstance(key, List) else [key]
        self.feature_alias = feature_alias if feature_alias else name
        # If no transformation is specified, default to referencing the a field with the same name
        if transform is None:
            self.transform = ExpressionTransformation(name)
        elif isinstance(transform, str):
            self.transform = ExpressionTransformation(transform)
        else:
            self.transform = transform
        default_key_alias = [k.key_column_alias for k in self.key]
        self.key_alias = key_alias if key_alias else default_key_alias
    
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

    def with_key(self, key_alias: Union[str, List[str]]) -> Feature:
        cleaned_key_alias=[key_alias] if isinstance(key_alias, str) else key_alias
        assert(len(cleaned_key_alias) == len(self.key))
        new_key = []
        for i in range(0, len(cleaned_key_alias)):
            typed_key = deepcopy(self.key[i])
            typed_key.key_column_alias=cleaned_key_alias[i]
            new_key.append(typed_key)

        res = deepcopy(self)
        res.key=new_key
        res.key_alias=cleaned_key_alias
        return res

    def as_feature(self, feature_alias) -> Feature:
        new_feature = deepcopy(self)
        new_feature.feature_alias=feature_alias
        return new_feature

    def to_feature_config(self) -> str:
        tm = Template("""
            {{feature.name}}: {
                def:{{feature.transform.to_feature_config()}}
                {{feature.feature_type.to_feature_config()}} 
            }
        """)
        return tm.render(feature=self)

