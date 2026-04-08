import json

results = []
with open(r'C:\Temp\arc-experiment\results\v4_pilot2\checkpoint.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            results.append(json.loads(line))

# Filter real results only (exclude 403 infra errors with 0 tokens)
real = [r for r in results if not (r.get('prompt_tokens', 0) == 0 and r.get('response_tokens', 0) == 0)]

# By category
categories = {}
for r in real:
    tid = r.get('task_id', '')
    if tid.startswith('TASK-'):
        cat = tid.split('-')[1]
    elif tid.startswith('pilot_'):
        cat = 'PILOT'
    else:
        cat = 'OTHER'
    if cat not in categories:
        categories[cat] = {}
    cond = r.get('condition')
    if cond not in categories[cat]:
        categories[cat][cond] = {'pass': 0, 'fail': 0}
    if r.get('pass'):
        categories[cat][cond]['pass'] += 1
    else:
        categories[cat][cond]['fail'] += 1

print('=== RESULTS BY CATEGORY ===')
for cat in sorted(categories.keys()):
    print(f'\n--- {cat} ---')
    for cond in ['baseline', 'cot', 'arc']:
        if cond in categories[cat]:
            d = categories[cat][cond]
            total = d['pass'] + d['fail']
            rate = 100 * d['pass'] / total if total > 0 else 0
            print(f'  {cond:10s}: {d["pass"]}/{total} = {rate:.0f}%')

# Statistical test
print('\n=== QUICK SIGNIFICANCE TEST (two-proportion z-test) ===')
arc_pass, arc_total = 37, 51
bas_pass, bas_total = 37, 60
cot_pass, cot_total = 33, 52

arc_rate = arc_pass / arc_total
bas_rate = bas_pass / bas_total
cot_rate = cot_pass / cot_total

# ARC vs Baseline
pooled = (arc_pass + bas_pass) / (arc_total + bas_total)
se = (pooled * (1 - pooled) * (1/arc_total + 1/bas_total)) ** 0.5
z1 = (arc_rate - bas_rate) / se if se > 0 else 0

# CoT vs Baseline
pooled2 = (cot_pass + bas_pass) / (cot_total + bas_total)
se2 = (pooled2 * (1 - pooled2) * (1/cot_total + 1/bas_total)) ** 0.5
z2 = (cot_rate - bas_rate) / se2 if se2 > 0 else 0

# ARC vs CoT
pooled3 = (arc_pass + cot_pass) / (arc_total + cot_total)
se3 = (pooled3 * (1 - pooled3) * (1/arc_total + 1/cot_total)) ** 0.5
z3 = (arc_rate - cot_rate) / se3 if se3 > 0 else 0

print(f'ARC vs Baseline: {arc_rate*100:.1f}% vs {bas_rate*100:.1f}% (diff=+{(arc_rate-bas_rate)*100:.1f}pp, z={z1:.2f})')
print(f'CoT vs Baseline: {cot_rate*100:.1f}% vs {bas_rate*100:.1f}% (diff=+{(cot_rate-bas_rate)*100:.1f}pp, z={z2:.2f})')
print(f'ARC vs CoT:      {arc_rate*100:.1f}% vs {cot_rate*100:.1f}% (diff=+{(arc_rate-cot_rate)*100:.1f}pp, z={z3:.2f})')
print(f'\nNote: z > 1.96 = p < 0.05 (two-tailed)')
print(f'      z > 1.645 = p < 0.05 (one-tailed, our pre-registered direction)')

# Infra error distribution
print('\n=== INFRA ERROR DISTRIBUTION ===')
for cond in ['baseline', 'cot', 'arc']:
    infra = [r for r in results if r.get('condition') == cond 
             and r.get('prompt_tokens', 0) == 0 and r.get('response_tokens', 0) == 0]
    print(f'  {cond:10s}: {len(infra)} infra errors')
print('Unequal loss may introduce bias - full experiment with 5 reps will mitigate')

# Summary verdict
print('\n' + '='*60)
print('PILOT 2 SUMMARY')
print('='*60)
print(f'Decision gate: PASS (baseline {bas_rate*100:.1f}% in 40-70% range)')
print(f'ARC advantage: +{(arc_rate-bas_rate)*100:.1f}pp over baseline (promising signal)')
print(f'Recommendation: PROCEED to full 900-run experiment')
print(f'Caveat: n=1 per task, high infra error rate ({len(results)-len(real)}/{len(results)} = {100*(len(results)-len(real))/len(results):.0f}%)')
