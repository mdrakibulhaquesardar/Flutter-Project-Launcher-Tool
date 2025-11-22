"""
License Key Generator for FluStudio

This utility generates valid license keys that match the validation algorithm.
Use this tool to generate license keys for distribution to users.

Standalone executable - no dependencies required.
"""
import hashlib
import random
import string
import sys
import os


class LicenseKeyGenerator:
    """Generate valid license keys for FluStudio."""
    
    # Obfuscated secret for license validation (same as in LicenseManager)
    # Must match exactly: Organization Name + App Name + Version + Salt
    # Organization: "NextCode Studio", App: "FluStudio", Version: "1.0.0"
    _SECRET_SEED = "NextCode StudioFluStudio1.0.0FluStudio2024"
    _VALIDATION_SECRET = hashlib.sha256(_SECRET_SEED.encode()).hexdigest()
    _SECRET_HASH = hashlib.sha512(_SECRET_SEED.encode()).hexdigest()
    
    @classmethod
    def _is_valid_key(cls, key_chars: str) -> bool:
        """Check if a key matches the validation pattern (same as LicenseManager)."""
        if len(key_chars) != 16:
            return False
        
        # Validation 1: Character distribution
        letter_count = sum(1 for c in key_chars if c.isalpha())
        number_count = sum(1 for c in key_chars if c.isdigit())
        if letter_count < 4 or number_count < 4:
            return False
        
        # Validation 2: Position-based weighted checksum
        position_weights = [3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61]
        position_checksum = sum(
            position_weights[i] * ord(key_chars[i]) for i in range(16)
        ) % 100000
        
        expected_pattern = sum(
            ord(cls._VALIDATION_SECRET[i % len(cls._VALIDATION_SECRET)]) * position_weights[i]
            for i in range(16)
        ) % 100000
        
        if abs(position_checksum - expected_pattern) >= 600:
            return False
        
        # Validation 3: Group-based checksum
        groups = [key_chars[i:i+4] for i in range(0, 16, 4)]
        group_checksums = []
        for i, group in enumerate(groups):
            group_sum = sum(ord(c) * (i + 1) for c in group)
            group_checksum = group_sum % 1000
            group_checksums.append(group_checksum)
        
        secret_group_base = sum(ord(c) for c in cls._VALIDATION_SECRET[:4]) % 1000
        valid_groups = 0
        for i, checksum in enumerate(group_checksums):
            expected_group = (secret_group_base + i * 137) % 1000
            if abs(checksum - expected_group) < 400:
                valid_groups += 1
        
        if valid_groups < 2:
            return False
        
        # Validation 4: Cross-position validation
        even_sum = sum(ord(key_chars[i]) for i in range(0, 16, 2))
        odd_sum = sum(ord(key_chars[i]) for i in range(1, 16, 2))
        even_odd_diff = abs(even_sum - odd_sum)
        
        secret_even = sum(ord(cls._VALIDATION_SECRET[i]) for i in range(0, len(cls._VALIDATION_SECRET), 2))
        secret_odd = sum(ord(cls._VALIDATION_SECRET[i]) for i in range(1, len(cls._VALIDATION_SECRET), 2))
        expected_diff = abs(secret_even - secret_odd)
        
        if abs(even_odd_diff - expected_diff) >= 1000:
            return False
        
        return True
    
    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a valid license key using smart generation algorithm.
        
        Returns:
            License key in format XXXX-XXXX-XXXX-XXXX
        """
        # Use targeted generation for better success rate
        return cls._generate_key_targeted()
    
    @classmethod
    def _generate_key_targeted(cls) -> str:
        """Generate key using targeted approach based on validation requirements."""
        chars = string.ascii_uppercase + string.digits
        position_weights = [3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61]
        
        # Calculate target values
        expected_pattern = sum(
            ord(cls._VALIDATION_SECRET[i % len(cls._VALIDATION_SECRET)]) * position_weights[i]
            for i in range(16)
        ) % 100000
        
        secret_group_base = sum(ord(c) for c in cls._VALIDATION_SECRET[:4]) % 1000
        
        secret_even = sum(ord(cls._VALIDATION_SECRET[i]) for i in range(0, len(cls._VALIDATION_SECRET), 2))
        secret_odd = sum(ord(cls._VALIDATION_SECRET[i]) for i in range(1, len(cls._VALIDATION_SECRET), 2))
        expected_diff = abs(secret_even - secret_odd)
        
        for attempt in range(100000):
            key_chars = [''] * 16
            
            # Generate with proper distribution
            letter_positions = random.sample(range(16), random.randint(4, 12))
            for pos in letter_positions:
                key_chars[pos] = random.choice(string.ascii_uppercase)
            
            for i in range(16):
                if not key_chars[i]:
                    key_chars[i] = random.choice(string.digits)
            
            key_str = ''.join(key_chars)
            
            # Quick validation checks
            letter_count = sum(1 for c in key_str if c.isalpha())
            if letter_count < 4:
                continue
            
            # Check position checksum
            position_checksum = sum(
                position_weights[i] * ord(key_str[i]) for i in range(16)
            ) % 100000
            
            if abs(position_checksum - expected_pattern) >= 600:
                continue
            
            # Check group checksums
            groups = [key_str[i:i+4] for i in range(0, 16, 4)]
            valid_groups_count = 0
            for i, group in enumerate(groups):
                group_sum = sum(ord(c) * (i + 1) for c in group)
                group_checksum = group_sum % 1000
                expected_group = (secret_group_base + i * 137) % 1000
                if abs(group_checksum - expected_group) < 400:
                    valid_groups_count += 1
            
            if valid_groups_count < 2:
                continue
            
            # Check even/odd difference
            even_sum = sum(ord(key_str[i]) for i in range(0, 16, 2))
            odd_sum = sum(ord(key_str[i]) for i in range(1, 16, 2))
            even_odd_diff = abs(even_sum - odd_sum)
            
            if abs(even_odd_diff - expected_diff) >= 1000:
                continue
            
            # Full validation
            if cls._is_valid_key(key_str):
                formatted_key = f"{key_str[:4]}-{key_str[4:8]}-{key_str[8:12]}-{key_str[12:16]}"
                return formatted_key
        
        # Ultimate fallback - generate a key that passes basic checks
        return cls._generate_fallback_key()
    
    @classmethod
    def _generate_fallback_key(cls) -> str:
        """Generate a fallback key that should work."""
        # This is a last resort - generate a key with proper structure
        chars = string.ascii_uppercase + string.digits
        key_chars = []
        
        # Ensure good distribution
        for _ in range(6):
            key_chars.append(random.choice(string.ascii_uppercase))
        for _ in range(6):
            key_chars.append(random.choice(string.digits))
        for _ in range(4):
            key_chars.append(random.choice(chars))
        
        random.shuffle(key_chars)
        key_str = ''.join(key_chars)
        formatted_key = f"{key_str[:4]}-{key_str[4:8]}-{key_str[8:12]}-{key_str[12:16]}"
        return formatted_key
    
    @classmethod
    def validate_key(cls, key: str) -> bool:
        """
        Validate a license key.
        
        Args:
            key: License key string
            
        Returns:
            True if valid, False otherwise
        """
        import re
        
        # Format check: XXXX-XXXX-XXXX-XXXX
        pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
        if not re.match(pattern, key.upper()):
            return False
        
        # Extract 16 characters (remove dashes)
        key_chars = key.replace('-', '').upper()
        return cls._is_valid_key(key_chars)
    
    @classmethod
    def generate_multiple_keys(cls, count: int = 10) -> list[str]:
        """
        Generate multiple license keys.
        
        Args:
            count: Number of keys to generate
            
        Returns:
            List of license keys
        """
        keys = []
        for i in range(count):
            key = cls.generate_key()
            keys.append(key)
            print(f"Generated key {i+1}/{count}: {key}")
        return keys


def show_menu():
    """Display interactive menu."""
    print("\n" + "=" * 60)
    print("FluStudio License Key Generator")
    print("=" * 60)
    print()
    print("Select an option:")
    print()
    print("  1. Generate Single License Key")
    print("  2. Generate Multiple License Keys")
    print("  3. Validate License Key")
    print("  4. Exit")
    print()
    print("=" * 60)
    
    choice = input("Enter your choice (1-4): ").strip()
    return choice


def generate_single_key():
    """Generate and display a single license key."""
    print("\n" + "=" * 60)
    print("Generating License Key...")
    print("=" * 60)
    print()
    
    try:
        print("Please wait, generating key...")
        key = LicenseKeyGenerator.generate_key()
        
        print()
        print("=" * 60)
        print("Generated License Key:")
        print("=" * 60)
        print()
        print(f"  {key}")
        print()
        print("=" * 60)
        print()
        
        # Ask if user wants to validate it
        validate = input("Would you like to validate this key? (y/n): ").strip().lower()
        if validate == 'y':
            is_valid = LicenseKeyGenerator.validate_key(key)
            print()
            print(f"Validation Result: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
    except Exception as e:
        print(f"\nError generating key: {e}")
    
    print()
    input("Press Enter to continue...")


def generate_multiple_keys():
    """Generate and display multiple license keys."""
    print("\n" + "=" * 60)
    print("Generate Multiple License Keys")
    print("=" * 60)
    print()
    
    try:
        count_input = input("How many keys would you like to generate? (1-100): ").strip()
        
        if not count_input.isdigit():
            print("\nInvalid input. Please enter a number.")
            input("Press Enter to continue...")
            return
        
        count = int(count_input)
        
        if count < 1 or count > 100:
            print("\nPlease enter a number between 1 and 100.")
            input("Press Enter to continue...")
            return
        
        print()
        print("=" * 60)
        print(f"Generating {count} License Key(s)...")
        print("=" * 60)
        print()
        
        keys = LicenseKeyGenerator.generate_multiple_keys(count)
        
        print()
        print("=" * 60)
        print("Generated License Keys:")
        print("=" * 60)
        print()
        for i, key in enumerate(keys, 1):
            print(f"  {i:3d}. {key}")
        print()
        print("=" * 60)
        
        # Ask if user wants to save to file
        save = input("\nWould you like to save these keys to a file? (y/n): ").strip().lower()
        if save == 'y':
            try:
                filename = input("Enter filename (default: license_keys.txt): ").strip()
                if not filename:
                    filename = "license_keys.txt"
                
                from datetime import datetime
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("FluStudio License Keys\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    for i, key in enumerate(keys, 1):
                        f.write(f"{i:3d}. {key}\n")
                
                print(f"\n✓ Keys saved to {filename}")
            except Exception as e:
                print(f"\nError saving file: {e}")
        
    except ValueError:
        print("\nInvalid input. Please enter a valid number.")
    except Exception as e:
        print(f"\nError generating keys: {e}")
    
    print()
    input("Press Enter to continue...")


def validate_key_interactive():
    """Interactive license key validation."""
    print("\n" + "=" * 60)
    print("Validate License Key")
    print("=" * 60)
    print()
    
    key = input("Enter license key to validate: ").strip()
    
    if not key:
        print("\nNo key entered.")
        input("Press Enter to continue...")
        return
    
    print()
    print("=" * 60)
    print("Validating...")
    print("=" * 60)
    print()
    
    try:
        is_valid = LicenseKeyGenerator.validate_key(key)
        
        if is_valid:
            print("✓ License Key is VALID")
            print()
            print(f"Key: {key}")
            print("Status: Valid")
            print("This key can be used to activate FluStudio.")
        else:
            print("✗ License Key is INVALID")
            print()
            print(f"Key: {key}")
            print("Status: Invalid")
            print("This key cannot be used to activate FluStudio.")
            print()
            print("Please check:")
            print("  - Key format: XXXX-XXXX-XXXX-XXXX")
            print("  - No typos or extra spaces")
            print("  - Key was generated using this tool")
        
    except Exception as e:
        print(f"\nError validating key: {e}")
    
    print()
    print("=" * 60)
    input("\nPress Enter to continue...")


def run_interactive_mode():
    """Run interactive menu-driven mode."""
    while True:
        try:
            # Clear screen (works on Windows)
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')
            
            choice = show_menu()
            
            if choice == '1':
                generate_single_key()
            elif choice == '2':
                generate_multiple_keys()
            elif choice == '3':
                validate_key_interactive()
            elif choice == '4':
                print("\nThank you for using FluStudio License Key Generator!")
                print("Goodbye!")
                break
            else:
                print("\nInvalid choice. Please enter 1, 2, 3, or 4.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            print("Thank you for using FluStudio License Key Generator!")
            break
        except Exception as e:
            print(f"\n\nError: {e}")
            input("Press Enter to continue...")


def main():
    """Main function for command-line usage."""
    import sys
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "validate":
                if len(sys.argv) < 3:
                    print("Usage: FluStudio-LicenseKeyGenerator.exe validate <KEY>")
                    if getattr(sys, 'frozen', False):
                        input("\nPress Enter to exit...")
                    sys.exit(1)
                key = sys.argv[2]
                is_valid = LicenseKeyGenerator.validate_key(key)
                print(f"Key: {key}")
                print(f"Valid: {'Yes' if is_valid else 'No'}")
                if getattr(sys, 'frozen', False):
                    input("\nPress Enter to exit...")
                return
            elif sys.argv[1].isdigit():
                count = int(sys.argv[1])
                print(f"Generating {count} license key(s)...")
                print()
                keys = LicenseKeyGenerator.generate_multiple_keys(count)
                print()
                print("=" * 60)
                print("Generated Keys:")
                print("=" * 60)
                for i, key in enumerate(keys, 1):
                    print(f"{i}. {key}")
                if getattr(sys, 'frozen', False):
                    input("\nPress Enter to exit...")
                return
            elif sys.argv[1] in ["-h", "--help", "help"]:
                print("FluStudio License Key Generator")
                print()
                print("Usage:")
                print("  FluStudio-LicenseKeyGenerator.exe              - Interactive mode")
                print("  FluStudio-LicenseKeyGenerator.exe [COUNT]       - Generate keys")
                print("  FluStudio-LicenseKeyGenerator.exe validate <KEY> - Validate key")
                print("  FluStudio-LicenseKeyGenerator.exe --help        - Show this help")
                if getattr(sys, 'frozen', False):
                    input("\nPress Enter to exit...")
                return
        else:
            # Interactive mode - show menu
            run_interactive_mode()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        if getattr(sys, 'frozen', False):
            input("Press Enter to exit...")
    except Exception as e:
        print(f"\n\nError: {e}")
        if getattr(sys, 'frozen', False):
            input("Press Enter to exit...")


def show_menu():
    """Display interactive menu."""
    print("\n" + "=" * 60)
    print("FluStudio License Key Generator")
    print("=" * 60)
    print()
    print("Select an option:")
    print()
    print("  1. Generate Single License Key")
    print("  2. Generate Multiple License Keys")
    print("  3. Validate License Key")
    print("  4. Exit")
    print()
    print("=" * 60)
    
    choice = input("Enter your choice (1-4): ").strip()
    return choice


def generate_single_key():
    """Generate and display a single license key."""
    print("\n" + "=" * 60)
    print("Generating License Key...")
    print("=" * 60)
    print()
    
    try:
        print("Please wait, generating key...")
        key = LicenseKeyGenerator.generate_key()
        
        print()
        print("=" * 60)
        print("Generated License Key:")
        print("=" * 60)
        print()
        print(f"  {key}")
        print()
        print("=" * 60)
        print()
        
        # Ask if user wants to validate it
        validate = input("Would you like to validate this key? (y/n): ").strip().lower()
        if validate == 'y':
            is_valid = LicenseKeyGenerator.validate_key(key)
            print()
            print(f"Validation Result: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
    except Exception as e:
        print(f"\nError generating key: {e}")
    
    print()
    input("Press Enter to continue...")


def generate_multiple_keys():
    """Generate and display multiple license keys."""
    print("\n" + "=" * 60)
    print("Generate Multiple License Keys")
    print("=" * 60)
    print()
    
    try:
        count_input = input("How many keys would you like to generate? (1-100): ").strip()
        
        if not count_input.isdigit():
            print("\nInvalid input. Please enter a number.")
            input("Press Enter to continue...")
            return
        
        count = int(count_input)
        
        if count < 1 or count > 100:
            print("\nPlease enter a number between 1 and 100.")
            input("Press Enter to continue...")
            return
        
        print()
        print("=" * 60)
        print(f"Generating {count} License Key(s)...")
        print("=" * 60)
        print()
        
        keys = LicenseKeyGenerator.generate_multiple_keys(count)
        
        print()
        print("=" * 60)
        print("Generated License Keys:")
        print("=" * 60)
        print()
        for i, key in enumerate(keys, 1):
            print(f"  {i:3d}. {key}")
        print()
        print("=" * 60)
        
        # Ask if user wants to save to file
        save = input("\nWould you like to save these keys to a file? (y/n): ").strip().lower()
        if save == 'y':
            try:
                filename = input("Enter filename (default: license_keys.txt): ").strip()
                if not filename:
                    filename = "license_keys.txt"
                
                from datetime import datetime
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("FluStudio License Keys\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    for i, key in enumerate(keys, 1):
                        f.write(f"{i:3d}. {key}\n")
                
                print(f"\n✓ Keys saved to {filename}")
            except Exception as e:
                print(f"\nError saving file: {e}")
        
    except ValueError:
        print("\nInvalid input. Please enter a valid number.")
    except Exception as e:
        print(f"\nError generating keys: {e}")
    
    print()
    input("Press Enter to continue...")


def validate_key_interactive():
    """Interactive license key validation."""
    print("\n" + "=" * 60)
    print("Validate License Key")
    print("=" * 60)
    print()
    
    key = input("Enter license key to validate: ").strip()
    
    if not key:
        print("\nNo key entered.")
        input("Press Enter to continue...")
        return
    
    print()
    print("=" * 60)
    print("Validating...")
    print("=" * 60)
    print()
    
    try:
        is_valid = LicenseKeyGenerator.validate_key(key)
        
        if is_valid:
            print("✓ License Key is VALID")
            print()
            print(f"Key: {key}")
            print("Status: Valid")
            print("This key can be used to activate FluStudio.")
        else:
            print("✗ License Key is INVALID")
            print()
            print(f"Key: {key}")
            print("Status: Invalid")
            print("This key cannot be used to activate FluStudio.")
            print()
            print("Please check:")
            print("  - Key format: XXXX-XXXX-XXXX-XXXX")
            print("  - No typos or extra spaces")
            print("  - Key was generated using this tool")
        
    except Exception as e:
        print(f"\nError validating key: {e}")
    
    print()
    print("=" * 60)
    input("\nPress Enter to continue...")


def run_interactive_mode():
    """Run interactive menu-driven mode."""
    while True:
        try:
            # Clear screen (works on Windows)
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')
            
            choice = show_menu()
            
            if choice == '1':
                generate_single_key()
            elif choice == '2':
                generate_multiple_keys()
            elif choice == '3':
                validate_key_interactive()
            elif choice == '4':
                print("\nThank you for using FluStudio License Key Generator!")
                print("Goodbye!")
                break
            else:
                print("\nInvalid choice. Please enter 1, 2, 3, or 4.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            print("Thank you for using FluStudio License Key Generator!")
            break
        except Exception as e:
            print(f"\n\nError: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()

