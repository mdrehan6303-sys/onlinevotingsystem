# blockchain.py
import hashlib
import time

class Block:
    def __init__(self, index, voter_hash, candidate_id, previous_hash, timestamp=None, current_hash=None):
        self.index = index
        self.voter_hash = voter_hash
        self.candidate_id = candidate_id
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp else str(time.time())
        
        if current_hash:
            self.current_hash = current_hash
        else:
            self.current_hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = str(self.index) + \
                     str(self.voter_hash) + \
                     str(self.candidate_id) + \
                     str(self.previous_hash) + \
                     str(self.timestamp)
        return hashlib.sha256(block_data.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(
            index=0,
            voter_hash="genesis",
            candidate_id=0,
            previous_hash="0"
        )
        self.chain.append(genesis)

    def get_last_block(self):
        return self.chain[-1]

    def add_vote(self, voter_hash, candidate_id):
        # Consensus simulation
        self._simulate_consensus()
        
        previous_hash = self.get_last_block().current_hash
        new_block = Block(
            index=len(self.chain),
            voter_hash=voter_hash,
            candidate_id=candidate_id,
            previous_hash=previous_hash
        )
        self.chain.append(new_block)
        return new_block
        
    def _simulate_consensus(self):
        """Simulate a Proof-of-Authority consensus across multiple nodes."""
        print("Broadcasting block to peer nodes...")
        time.sleep(0.1) # Simulate network delay
        print("Node 1: Validated ✓")
        print("Node 2: Validated ✓")
        print("Node 3: Validated ✓")
        print("Consensus Reached! Appending to blockchain.")

    def restore_block(self, index, voter_hash, candidate_id, previous_hash, timestamp, current_hash):
        """Used to rebuild the chain from database safely."""
        block = Block(
            index=index,
            voter_hash=voter_hash,
            candidate_id=candidate_id,
            previous_hash=previous_hash,
            timestamp=timestamp,
            current_hash=current_hash
        )
        # Avoid duplicating genesis
        if index == 0 and len(self.chain) > 0:
            self.chain[0] = block
        else:
            self.chain.append(block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.current_hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.current_hash:
                return False

        return True
