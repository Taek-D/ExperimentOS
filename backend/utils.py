import json
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def sanitize(obj):
    """Convert numpy types to native Python types and replace NaN/Inf with None."""
    text = json.dumps(obj, cls=NumpyEncoder, allow_nan=True)
    return json.loads(text, parse_constant=lambda _: None)
