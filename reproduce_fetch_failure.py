from unittest.mock import MagicMock, patch
import sys
import traceback

# Add src to path if needed (might be handled by current dir)
sys.path.append(".")

from src.experimentos.integrations.statsig import StatsigProvider, IntegrationVariant, IntegrationResult

def reproduce():
    print("Starting reproduction...")
    statsig_provider = StatsigProvider(api_key="test_secret_key")
    
    mock_data = {
        "message": "success",
        "data": {
            "id": "exp_123",
            "results": [
                {
                    "name": "Control",
                    "exposures": 1000,
                    "conversions": 100,
                    "metrics": {"revenue": 5000.0, "clicks": 200.0}
                },
                {
                    "name": "Treatment",
                    "exposures": 1000,
                    "conversions": 120, 
                    "metrics": {"revenue": 6000.0, "clicks": 250.0}
                }
            ]
        }
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        
        mock_client.get.return_value = mock_response

        # Execute
        try:
            result = statsig_provider.fetch_experiment("exp_123")
            print("Success!")
            print(result)
        except Exception as e:
            print("Caught exception:")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        reproduce()
    except Exception as e:
        print(f"Top level error: {e}")
        traceback.print_exc()
