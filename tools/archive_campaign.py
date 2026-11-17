#!/usr/bin/env python3
"""Losslessly archive a completed campaign's raw observations, preserving every byte hash."""
import argparse
import json
from pathlib import Path
from benchmark_suite import archive_evidence, validate_campaign

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign',type=Path)
    args=parser.parse_args()
    record=json.loads((args.campaign/'campaign.json').read_text())
    validate_campaign(args.campaign,record)
    archive_evidence(args.campaign)
    validate_campaign(args.campaign,record)
    print(f'Archived and verified: {args.campaign}')
