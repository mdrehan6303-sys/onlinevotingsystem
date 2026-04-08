# blockchain.py
# This file creates and manages the blockchain for storing votes

import hashlib  # Used for SHA-256 hashing
import json     # Used to convert data to string format
import time     # Used to record the time of each vote

class Block:
    """
    A Block is like one page in a notebook.
    Each page contains one vote and is linked to the previous page.
    """
    def __init__(self, index, voter_hash, candidate_id, previous_hash):
        # Block number (1st vote, 2nd vote, etc.)
        self.index = index
        
        # The voter's identity (hidden using SHA hash for privacy)
        self.voter_hash = voter_hash
        
        # Which candidate was voted for
        self.candidate_id = candidate_id
        
        # Hash of the previous block (this links blocks together)
        self.previous_hash = previous_hash
        
        # Time when this vote was cast
        self.timestamp = str(time.time())
        
        # This block's own unique hash (created from all above data)
        self.current_hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Creates a unique fingerprint for this block.
        If anyone changes any data, this fingerprint will change.
        """
        # Combine all block data into one string
        block_data = str(self.index) + \
                     str(self.voter_hash) + \
                     str(self.candidate_id) + \
                     str(self.previous_hash) + \
                     str(self.timestamp)
        
        # Convert to SHA-256 hash and return
        return hashlib.sha256(block_data.encode()).hexdigest()


class Blockchain:
    """
    Blockchain is like a notebook made of many linked pages (blocks).
    Each page links to the previous one, making it tamper-proof.
    """
    def __init__(self):
        # Start with an empty chain
        self.chain = []
        
        # Create the very first block (called Genesis Block)
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Genesis block is the FIRST block in the chain.
        It has no previous block, so previous_hash is '0'.
        Think of it as the first page of a brand new notebook.
        """
        genesis = Block(
            index=0,
            voter_hash="genesis",
            candidate_id=0,
            previous_hash="0"
        )
        self.chain.append(genesis)

    def get_last_block(self):
        """Returns the most recently added block"""
        return self.chain[-1]

    def add_vote(self, voter_hash, candidate_id):
        """
        Adds a new vote to the blockchain.
        Each new block links to the previous block's hash.
        """
        # Get the hash of the last block
        previous_hash = self.get_last_block().current_hash
        
        # Create a new block with the vote
        new_block = Block(
            index=len(self.chain),
            voter_hash=voter_hash,
            candidate_id=candidate_id,
            previous_hash=previous_hash
        )
        
        # Add the block to the chain
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """
        Checks if the blockchain has been tampered with.
        Goes through every block and verifies:
        1. Each block's hash is correct
        2. Each block correctly links to the previous block
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check if current block's hash is still valid
            if current.current_hash != current.calculate_hash():
                return False  # Someone changed the vote data!

            # Check if the link to previous block is correct
            if current.previous_hash != previous.current_hash:
                return False  # Chain is broken — tampering detected!

        return True  # Everything is fine
