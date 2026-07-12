import regex as re
pattern = r"'(?:[smdt]|ll|ve|re)| ?\w+| ?[^\w\s]+|\s+"

def chunkize(text):
    chunks = re.findall(pattern, text)
    return chunks

text = "Hello there! What's up?? café"
# print(chunkize(text))

def preprocess(text):
    chunks = chunkize(text)
    byte_chunks = []
    for chunk in chunks:
        byte_chunk = list(chunk.encode("utf-8"))
        byte_chunks.append(byte_chunk)
    return byte_chunks

# print(preprocess(text)[-1])

def pair_counts(byte_chunks):
    pairs = dict()
    for byte_chunk in byte_chunks:
        for i in range(len(byte_chunk)-1):
            token_a, token_b = byte_chunk[i], byte_chunk[i+1]
            pairs[(token_a, token_b)] = pairs.get((token_a, token_b), 0)+1
    return pairs


def merge(byte_chunks, merge_id, encode_rules, decode_dict, pairs, counter=0):
    if len(pairs) == 0:
        pairs |= pair_counts(byte_chunks)
        counter += 1
    max_pair = None
    max_count = 0
    for pair, count in pairs.items():
        if count > max_count:
            max_pair = pair
            max_count = count
    if max_pair:
        for byte_chunk in byte_chunks:
            for i in range(len(byte_chunk)-2, -1, -1):
                token_a, token_b = byte_chunk[i], byte_chunk[i+1]
                if token_a == max_pair[0] and token_b == max_pair[1]:
                    if i > 0:
                        pairs[(byte_chunk[i-1], byte_chunk[i])] -= 1
                    if i < len(byte_chunk)-2:
                        pairs[(byte_chunk[i+1], byte_chunk[i+2])] -= 1
                    byte_chunk[i] = merge_id
                    byte_chunk.pop(i+1)
                    pairs[(token_a, token_b)] -= 1
                    if i < len(byte_chunk)-1:
                        pairs[(merge_id, byte_chunk[i+1])] = pairs.get((merge_id, byte_chunk[i+1]), 0)+1
                    if i > 0:
                        pairs[(byte_chunk[i-1], merge_id)] = pairs.get((byte_chunk[i-1], merge_id), 0)+1

        encode_rules.append((max_pair[0], max_pair[1], merge_id))
        decode_dict[merge_id] = decode_dict[max_pair[0]]+decode_dict[max_pair[1]]
        return True, counter
    return False, counter
    
class BPETokenizer():
    def __init__(self, vocab_size):
        self.vocab_size = vocab_size
        self.encode_rules = []
        self.decode_dict = dict()
        self.default_dict = {i:(i,) for i in range(256)}
        self.pairs = dict()

    def train(self, text):
        counter = 0
        self.encode_rules.clear()
        self.decode_dict = self.default_dict.copy()
        self.pairs.clear()
        byte_chunks = preprocess(text)
        for i in range(self.vocab_size-256):
            merge_id = 256+i
            merged, count = merge(byte_chunks, merge_id, self.encode_rules, self.decode_dict, self.pairs)
            counter += count
            if merged == False:
                break
        print(f"Number of byte-pair scans over entire data = {counter}")

    def _encode_chunks(self, text):
        enc_byte_chunks = preprocess(text)
        for rule in self.encode_rules:
            a, b, merge_id = rule
            for byte_chunk in enc_byte_chunks:
                for i in range(len(byte_chunk)-2, -1, -1):
                    token_a, token_b = byte_chunk[i], byte_chunk[i+1]
                    if token_a == a and token_b == b:
                        byte_chunk[i] = merge_id
                        byte_chunk.pop(i+1)
        return enc_byte_chunks
    
    def encode(self, text):
        byte_chunks = self._encode_chunks(text)
        tokens = []
        for chunk in byte_chunks:
            tokens.extend(chunk)
        return tokens
    
    
    def decode(self, tokens : list):
        decoded_tokens = []
        for token in tokens:
            decoded = self.decode_dict[token]
            decoded_tokens.extend(list(decoded))
        result = bytes(decoded_tokens).decode("utf-8")
        return result
    

# import urllib.request
# urllib.request.urlretrieve(
#     "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
#     "tiny_shakespeare.txt"
# )

# text = ""
# with open("tiny_shakespeare.txt", 'r', encoding='utf-8') as f:
#     for line in f:
#         text += line

# import time
# tokenizer = BPETokenizer(vocab_size=1000)
# start = time.time()
# tokenizer.train(text)
# print(time.time()-start)
# print(tokenizer.decode(tokenizer.encode("HELLo anAkin!!1")))
# # Executed in 24.22 sec
