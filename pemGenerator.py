def save_plaintext_key_to_pem(plaintext_key, pem_file_path):
    # Add PEM headers and footers
    pem_formatted_key = "-----BEGIN PUBLIC KEY-----\n"
    
    # Wrap the plaintext key at 64 characters per line
    for i in range(0, len(plaintext_key), 64):
        pem_formatted_key += plaintext_key[i:i+64] + "\n"
    
    pem_formatted_key += "-----END PUBLIC KEY-----\n"
    
    # Save to a PEM file
    with open(pem_file_path, "w") as pem_file:
        pem_file.write(pem_formatted_key)

# Example plaintext key (replace this with your actual key)
plaintext_key = "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEEVs/o5+uQbTjL3chynL4wXgUg2R9q9UU8I5mEovUf86QZ7kOBIjJwqnzD1omageEHWwHdBO6B+dFabmdT9POxg=="

# File path to save the PEM file
pem_file_path = "/Users/samuelkajiwara/Desktop/public_key.pem"

# Save the plaintext key as a PEM file
save_plaintext_key_to_pem(plaintext_key, pem_file_path)
print(f"Public key saved to {pem_file_path}")