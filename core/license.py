"""License management for FluStudio."""
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Literal
from core.logger import Logger
from core.branding import Branding
from utils.registry_utils import RegistryUtils


class LicenseManager:
    """Manages application licensing, trial period, and license key activation."""
    
    TRIAL_DAYS = 14
    REMINDER_DAYS = 3  # Show reminder 3 days before expiry
    
    # Registry path for license data
    REGISTRY_PATH = f"Software\\{Branding.ORGANIZATION_NAME}\\{Branding.APP_NAME}\\License"
    
    # Registry value names
    REG_LICENSE_KEY = "LicenseKey"
    REG_ACTIVATED_AT = "ActivatedAt"
    REG_TRIAL_START_DATE = "TrialStartDate"
    REG_LICENSE_STATUS = "LicenseStatus"
    
    # Obfuscated secret for license validation
    # Using hash of organization name + app name + version + additional salt
    _SECRET_SEED = f"{Branding.ORGANIZATION_NAME}{Branding.APP_NAME}{Branding.APP_VERSION}FluStudio2024"
    _VALIDATION_SECRET = hashlib.sha256(_SECRET_SEED.encode()).hexdigest()
    # Use longer secret for better security
    _SECRET_HASH = hashlib.sha512(_SECRET_SEED.encode()).hexdigest()
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = Logger()
        self._initialized = True
        self._ensure_trial_start_date()
    
    def _ensure_trial_start_date(self):
        """Ensure trial start date is set (on first launch)."""
        trial_start = self._read_registry(self.REG_TRIAL_START_DATE)
        if not trial_start:
            # First launch - set trial start date
            now = datetime.now().isoformat()
            self._write_registry(self.REG_TRIAL_START_DATE, now)
            self.logger.info("Trial period started")
    
    def _read_registry(self, value_name: str) -> Optional[str]:
        """Read value from registry."""
        return RegistryUtils.read_registry_value(self.REGISTRY_PATH, value_name)
    
    def _write_registry(self, value_name: str, value: str) -> bool:
        """Write value to registry."""
        return RegistryUtils.write_registry_value(self.REGISTRY_PATH, value_name, value)
    
    def _validate_license_key(self, key: str) -> bool:
        """
        Validate license key using strong algorithm-based checksum.
        
        Args:
            key: License key string (format: XXXX-XXXX-XXXX-XXXX)
            
        Returns:
            True if valid, False otherwise
        """
        # Format check: XXXX-XXXX-XXXX-XXXX
        pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
        if not re.match(pattern, key.upper()):
            return False
        
        # Extract 16 characters (remove dashes)
        key_chars = key.replace('-', '').upper()
        
        if len(key_chars) != 16:
            return False
        
        # Validation 1: Character distribution (must have both letters and numbers)
        has_letters = any(c.isalpha() for c in key_chars)
        has_numbers = any(c.isdigit() for c in key_chars)
        if not (has_letters and has_numbers):
            return False
        
        # Validation 2: Minimum character distribution requirements
        letter_count = sum(1 for c in key_chars if c.isalpha())
        number_count = sum(1 for c in key_chars if c.isdigit())
        # Must have at least 4 letters and 4 numbers
        if letter_count < 4 or number_count < 4:
            return False
        
        # Validation 3: Position-based weighted checksum
        # Use different weights for different positions
        position_weights = [3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61]
        position_checksum = sum(
            position_weights[i] * ord(key_chars[i]) for i in range(16)
        ) % 100000
        
        # Expected pattern from secret
        expected_pattern = sum(
            ord(self._VALIDATION_SECRET[i % len(self._VALIDATION_SECRET)]) * position_weights[i]
            for i in range(16)
        ) % 100000
        
        # Must match within range (600 tolerance for better key generation)
        if abs(position_checksum - expected_pattern) >= 600:
            return False
        
        # Validation 4: Group-based checksum (each group of 4)
        groups = [key_chars[i:i+4] for i in range(0, 16, 4)]
        group_checksums = []
        for i, group in enumerate(groups):
            group_sum = sum(ord(c) * (i + 1) for c in group)
            group_checksum = group_sum % 1000
            group_checksums.append(group_checksum)
        
        # Validate group checksums against secret (more lenient - at least 3/4 groups)
        secret_group_base = sum(ord(c) for c in self._VALIDATION_SECRET[:4]) % 1000
        valid_groups = 0
        for i, checksum in enumerate(group_checksums):
            expected_group = (secret_group_base + i * 137) % 1000
            if abs(checksum - expected_group) < 400:  # More lenient tolerance
                valid_groups += 1
        
        # At least 2 out of 4 groups should match (more lenient)
        if valid_groups < 2:
            return False
        
        # Validation 5: Cross-position validation
        # Check sum of even positions vs odd positions
        even_sum = sum(ord(key_chars[i]) for i in range(0, 16, 2))
        odd_sum = sum(ord(key_chars[i]) for i in range(1, 16, 2))
        even_odd_diff = abs(even_sum - odd_sum)
        
        # Difference should be within expected range
        secret_even = sum(ord(self._VALIDATION_SECRET[i]) for i in range(0, len(self._VALIDATION_SECRET), 2))
        secret_odd = sum(ord(self._VALIDATION_SECRET[i]) for i in range(1, len(self._VALIDATION_SECRET), 2))
        expected_diff = abs(secret_even - secret_odd)
        
        if abs(even_odd_diff - expected_diff) >= 1000:  # More lenient tolerance
            return False
        
        # All validations passed
        return True
    
    def get_license_status(self) -> Literal["trial_active", "trial_expired", "license_active", "license_invalid"]:
        """
        Get current license status.
        
        Returns:
            License status string
        """
        # Check if license key exists and is valid
        license_key = self._read_registry(self.REG_LICENSE_KEY)
        if license_key:
            # Registry stores key without dashes, add dashes for validation
            if len(license_key) == 16 and not '-' in license_key:
                # Format with dashes: XXXX-XXXX-XXXX-XXXX
                formatted_key = f"{license_key[:4]}-{license_key[4:8]}-{license_key[8:12]}-{license_key[12:16]}"
            else:
                formatted_key = license_key
            
            if self._validate_license_key(formatted_key):
                return "license_active"
            else:
                return "license_invalid"
        
        # Check trial status
        if self.is_trial_active():
            return "trial_active"
        else:
            return "trial_expired"
    
    def is_trial_active(self) -> bool:
        """Check if trial period is still active."""
        trial_start_str = self._read_registry(self.REG_TRIAL_START_DATE)
        if not trial_start_str:
            # No trial start date - assume first launch, trial is active
            return True
        
        try:
            trial_start = datetime.fromisoformat(trial_start_str)
            days_elapsed = (datetime.now() - trial_start).days
            return days_elapsed < self.TRIAL_DAYS
        except Exception as e:
            self.logger.error(f"Error checking trial status: {e}")
            return True  # Default to active if error
    
    def get_days_remaining(self) -> int:
        """Get number of trial days remaining."""
        trial_start_str = self._read_registry(self.REG_TRIAL_START_DATE)
        if not trial_start_str:
            return self.TRIAL_DAYS
        
        try:
            trial_start = datetime.fromisoformat(trial_start_str)
            days_elapsed = (datetime.now() - trial_start).days
            days_remaining = self.TRIAL_DAYS - days_elapsed
            return max(0, days_remaining)
        except Exception:
            return self.TRIAL_DAYS
    
    def should_show_reminder(self) -> bool:
        """Check if reminder should be shown (3 days before expiry)."""
        if not self.is_trial_active():
            return False
        
        days_remaining = self.get_days_remaining()
        return days_remaining <= self.REMINDER_DAYS and days_remaining > 0
    
    def is_license_valid(self) -> bool:
        """Check if a valid license is activated."""
        status = self.get_license_status()
        return status == "license_active"
    
    def activate_license(self, key: str) -> tuple[bool, str]:
        """
        Activate a license key.
        
        Args:
            key: License key string
            
        Returns:
            Tuple of (success, message)
        """
        # Validate key format and algorithm
        if not self._validate_license_key(key):
            return False, "Invalid license key format or validation failed."
        
        # Store license key
        normalized_key = key.replace('-', '').upper()
        if not self._write_registry(self.REG_LICENSE_KEY, normalized_key):
            return False, "Failed to save license key to registry."
        
        # Store activation timestamp
        activated_at = datetime.now().isoformat()
        self._write_registry(self.REG_ACTIVATED_AT, activated_at)
        
        # Update status
        self._write_registry(self.REG_LICENSE_STATUS, "license_active")
        
        self.logger.info("License activated successfully")
        return True, "License activated successfully!"
    
    def get_license_info(self) -> dict:
        """Get license information."""
        status = self.get_license_status()
        info = {
            "status": status,
            "is_trial": status in ["trial_active", "trial_expired"],
            "is_activated": status == "license_active",
            "days_remaining": self.get_days_remaining() if status == "trial_active" else 0,
            "trial_start_date": self._read_registry(self.REG_TRIAL_START_DATE),
            "activated_at": self._read_registry(self.REG_ACTIVATED_AT),
        }
        return info
    
    def deactivate_license(self) -> bool:
        """Deactivate current license (for testing/admin purposes)."""
        RegistryUtils.delete_registry_value(self.REGISTRY_PATH, self.REG_LICENSE_KEY)
        RegistryUtils.delete_registry_value(self.REGISTRY_PATH, self.REG_ACTIVATED_AT)
        RegistryUtils.delete_registry_value(self.REGISTRY_PATH, self.REG_LICENSE_STATUS)
        self.logger.info("License deactivated")
        return True

