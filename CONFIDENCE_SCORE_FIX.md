# Confidence Score Fix - Real Data Based Calculation

## Problem Identified

**FLAN-T5 does NOT generate confidence scores!**

### Issues:
1. ❌ FLAN-T5 is a text generation model, not a confidence-scoring model
2. ❌ Current code tries to extract confidence from FLAN-T5 output using regex
3. ❌ FLAN-T5 doesn't output confidence scores in its responses
4. ❌ When confidence not found, it defaults to 0.5 (random)
5. ❌ Confidence is NOT based on actual file data quality

### Current Flow (WRONG):
```
FLAN-T5 generates text → Try to extract "Confidence: X" → Not found → Default 0.5
```

## Solution Implemented

### Real Confidence Calculator (`confidence_calculator.py`)

**Calculates confidence based on ACTUAL data:**

1. **Log File Quality (40% weight)**
   - Number of log files uploaded
   - Number of processed logs
   - Error patterns found in logs
   - Log content size/quality

2. **Incident Completeness (20% weight)**
   - Title quality
   - Description length and detail
   - Severity specified
   - Category specified
   - Affected services listed
   - Assignment status

3. **Similarity to Past Incidents (15% weight)**
   - Similar incidents found
   - Similarity score (>0.7 = high, >0.5 = medium, >0.3 = low)

4. **Rule-Based Analysis Success (15% weight)**
   - Root cause found in logs = 0.6
   - Root cause found in description = 0.5
   - Root cause found in title = 0.4
   - Default = 0.3

5. **Root Cause Found in Logs (10% weight)**
   - Bonus if root cause was identified from log files

### Formula:
```
Total Confidence = 
  (Log Quality × 0.4) +
  (Completeness × 0.2) +
  (Similarity Boost × 0.15) +
  (Rule-Based × 0.15) +
  (Log Found Bonus × 0.1)
```

## Examples

### Example 1: High Confidence (0.75)
- ✅ 3 log files uploaded and processed
- ✅ Errors found in logs (database pool exhausted)
- ✅ Detailed description (100+ chars)
- ✅ Category and severity specified
- ✅ Similar past incidents found (similarity: 0.8)
- ✅ Root cause found in logs

### Example 2: Medium Confidence (0.50)
- ✅ 1 log file uploaded
- ✅ Basic description (50 chars)
- ✅ Category specified
- ❌ No similar incidents
- ✅ Root cause found in description

### Example 3: Low Confidence (0.30)
- ❌ No log files
- ✅ Basic title only
- ❌ No description
- ❌ No category
- ❌ No similar incidents
- ❌ Root cause inferred from title only

## How It Works Now

1. **Files Uploaded** → Logs processed
2. **AI Analysis** → Root cause generated
3. **Real Confidence Calculated** → Based on actual data quality
4. **Confidence Saved** → Real score, not fake FLAN-T5 score

## Benefits

✅ **Accurate confidence** - Based on real data, not random numbers
✅ **File-based** - More files = higher confidence
✅ **Quality-aware** - Better logs = higher confidence
✅ **Transparent** - Can explain why confidence is high/low
✅ **Real-time** - Updates when files are uploaded

## Files Modified

1. **`incidents/services/confidence_calculator.py`** - NEW
   - Real confidence calculation
   - Multiple factors considered
   - Quality-based scoring

2. **`incidents/tasks.py`** - IMPROVED
   - Uses real confidence calculator
   - Blends AI confidence (if reasonable) with real confidence
   - Checks if root cause found in logs

## Testing

To verify confidence is correct:

1. **Upload multiple log files** → Confidence should increase
2. **Add detailed description** → Confidence should increase
3. **Specify category/severity** → Confidence should increase
4. **Check similar incidents** → Confidence should increase if found
5. **No logs, minimal info** → Confidence should be low (0.3-0.4)

## Confidence Score Ranges

- **0.7 - 1.0**: High confidence (good logs + complete info + similar incidents)
- **0.5 - 0.7**: Medium confidence (some logs + basic info)
- **0.3 - 0.5**: Low confidence (minimal info, no logs)
- **0.0 - 0.3**: Very low confidence (incomplete data)

## Important Note

**FLAN-T5 confidence is ignored** - We now calculate real confidence based on:
- Actual file data
- Log quality
- Information completeness
- Similarity to past incidents

The confidence bar now shows **real, meaningful scores** based on your actual incident data!

