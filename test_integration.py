"""
Test script for iTunes integration with iPod playlists.

This script reads playlists from the connected iPod and processes:
- Songs in "On-The-Go 2" and "On-The-Go 3" -> Approved (moved to library)
- All other discovered songs -> Rejected (deleted)
"""

import sys
from src.itunes_integrator import iTunesIntegrator
from src.utils import setup_logging

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logger = setup_logging(__name__, 'test_integration.log')

def main():
    """Run iTunes integration with iPod playlists."""

    # Initialize with your iPod playlists
    playlist_names = ["On-The-Go 2", "On-The-Go 3"]

    logger.info("="*80)
    logger.info("TESTING ITUNES INTEGRATION FROM IPOD")
    logger.info(f"Approval playlists: {playlist_names}")
    logger.info("="*80)

    try:
        # Create integrator with iPod source
        integrator = iTunesIntegrator(playlist_names=playlist_names, use_ipod=True)

        # Run the integration workflow
        approved, rejected = integrator.run()

        print("\n" + "="*80)
        print("INTEGRATION COMPLETE!")
        print("="*80)
        print(f"[+] Approved songs: {approved}")
        print(f"[-] Rejected songs: {rejected}")
        print("="*80)
        print("\nNext steps:")
        print("1. Check logs/itunes_integrator.log for detailed results")
        print("2. Check music/library/ for approved songs (permanent)")
        print("3. Check music/staging/ for approved songs (ready for iTunes)")
        print("4. Drag music/staging/ into iTunes to organize")
        print("5. Run 'python -m src.music_discovery' for next batch of recommendations")
        print("="*80)

    except Exception as e:
        logger.error(f"Integration failed: {e}")
        print(f"\n[ERROR] {e}")
        print("Check logs/itunes_integrator.log for details")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
