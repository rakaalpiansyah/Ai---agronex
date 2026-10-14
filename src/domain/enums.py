from enum import Enum


class FAOClass(str, Enum):
    """FAO Land Suitability Classification order and classes."""
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    N = "N"

    @classmethod
    def from_score(cls, score: float) -> "FAOClass":
        if score >= 0.80:
            return cls.S1
        elif score >= 0.60:
            return cls.S2
        elif score >= 0.40:
            return cls.S3
        return cls.N

    @property
    def label_id(self) -> str:
        descriptions = {
            "S1": "Sangat Sesuai",
            "S2": "Cukup Sesuai",
            "S3": "Sesuai Marginal",
            "N": "Tidak Sesuai"
        }
        return descriptions.get(self.value, "Tidak Diketahui")


class SensorMetric(str, Enum):
    """Physical telemetry metrics captured by field IoT devices."""
    SOIL_MOISTURE_VWC = "soil_moisture_vwc"
    SOIL_TEMPERATURE = "soil_temperature"
    SOIL_PH = "soil_ph"
    SOIL_EC = "soil_ec"
    SOIL_N = "soil_n"
    SOIL_P = "soil_p"
    SOIL_K = "soil_k"
    AIR_TEMPERATURE = "air_temperature"
    AIR_HUMIDITY = "air_humidity"
    RAINFALL = "rainfall"
    SOLAR_RADIATION = "solar_radiation"
    WIND_SPEED = "wind_speed"


class SoilType(str, Enum):
    CLAY = "clay"
    LOAM = "loam"
    SANDY_LOAM = "sandy_loam"
    SAND = "sand"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationStatus(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_AGRONOMIST_REVIEW = "NEEDS_AGRONOMIST_REVIEW"
    REJECTED_LOW_DATA = "REJECTED_LOW_DATA"
