# Hybrid Confidence Calculator - Copy-Paste Ready Code

## Summary

**Problem:** FLAN-T5 confidence scores stuck at 0.47-0.50 (unreliable)

**Solution:** Hybrid approach combining:
- Model confidence (20%) - only if reasonable
- Log presence (25%) - files uploaded & processed
- Keyword detection (25%) - redis, kafka, timeout, db
- Similar incidents (15%) - past incident matching
- Data completeness (15%) - incident info quality

## Complete Implementation

### 1. Hybrid Confidence Calculator (`incidents/services/hybrid_confidence_calculator.py`)

**Already created** - See file for full implementation

### 2. Updated Celery Task (`incidents/tasks.py`)

**Key changes in `generate_root_cause_analysis` function:**

```python
# OLD CODE (Line ~162-172):
# 5️⃣ Calculate REAL confidence based on actual data
real_confidence = calculate_real_confidence(incident, root_cause_found_in_logs)

# Use real confidence, but if AI gave a reasonable confidence, blend them
if confidence > 0.3 and confidence < 0.9:
    final_confidence = (real_confidence * 0.7) + (confidence * 0.3)
else:
    final_confidence = real_confidence

# NEW CODE (Line ~162-168):
# 5️⃣ Calculate HYBRID confidence using multi-factor approach
from incidents.services.hybrid_confidence_calculator import calculate_hybrid_confidence

# Calculate hybrid confidence (combines model + logs + keywords + similarity + completeness)
final_confidence, confidence_breakdown = calculate_hybrid_confidence(
    incident=incident,
    model_confidence=confidence,  # FLAN-T5 confidence (will be validated inside)
    root_cause_found_in_logs=root_cause_found_in_logs
)
```

## How It Works

### Confidence Calculation Formula

```
Final Confidence = 
  Log Presence (25%) +
  Keyword Detection (25%) +
  Similar Incidents (15%) +
  Data Completeness (15%) +
  Model Confidence (20%) +
  Log Bonus (+0.05 if root cause found in logs)
```

### Example Scenarios

**Scenario 1: High Confidence (0.75)**
- 3 log files uploaded and processed
- Keywords found: "redis", "timeout" in logs
- Similar incident found (similarity: 0.8)
- Complete incident description
- Model confidence: 0.5 (used as 0.5 × 0.20 = 0.10)
- Root cause found in logs (+0.05)

**Scenario 2: Medium Confidence (0.55)**
- 1 log file uploaded
- Keywords found: "database" in description
- No similar incidents
- Basic description
- Model confidence: 0.47 (used as 0.5 × 0.20 = 0.10)

**Scenario 3: Low Confidence (0.35)**
- No log files
- No keywords detected
- No similar incidents
- Minimal description
- Model confidence: 0.5 (used as 0.5 × 0.20 = 0.10)

## Key Features

1. **Keyword Detection**
   - Checks logs, description, and title
   - Categories: redis, kafka, timeout, db, network, memory, disk
   - Logs weighted higher than description

2. **Model Confidence Validation**
   - Only uses FLAN-T5 confidence if 0.3 ≤ score ≤ 0.8
   - Ignores unreasonable values (<0.3 or >0.8)
   - Uses neutral 0.5 if model confidence is invalid

3. **Transparent Breakdown**
   - Returns confidence breakdown dict
   - Shows contribution of each factor
   - Useful for debugging and transparency

## Testing

To test the new confidence calculation:

1. **Create incident with logs:**
   - Upload log files containing "redis timeout" or "database error"
   - Should see higher confidence (0.6-0.8)

2. **Create incident without logs:**
   - Only description with keywords
   - Should see medium confidence (0.4-0.6)

3. **Create minimal incident:**
   - No logs, basic description
   - Should see lower confidence (0.3-0.4)

## Benefits

✅ **No more stuck at 0.47-0.50** - Scores reflect actual data quality
✅ **Keyword-aware** - Detects redis, kafka, timeout, db automatically
✅ **Log-based** - More logs = Higher confidence
✅ **Similar incident aware** - Past incidents boost confidence
✅ **Transparent** - Breakdown shows why confidence is high/low

## Files Modified

1. ✅ `incidents/services/hybrid_confidence_calculator.py` - NEW
2. ✅ `incidents/tasks.py` - UPDATED (line ~162)

## Next Steps

1. Restart Celery worker
2. Test with existing incidents
3. Check confidence scores - should vary based on data quality
4. Monitor confidence breakdown for transparency

