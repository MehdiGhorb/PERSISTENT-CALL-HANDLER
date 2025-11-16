"""
LiveKit SIP Management - Simplified for persistent call handling
"""
import asyncio
from typing import Dict, Optional
from livekit import api

from services.logging_config import get_logger
from config import get_settings

class LiveKitManager:
    """Manages LiveKit SIP trunks and dispatch rules for persistent phone numbers"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.api_client: Optional[api.LiveKitAPI] = None
        self.trunk_ids: Dict[str, str] = {}  # phone_number -> trunk_id
        self.dispatch_rule_ids: Dict[str, str] = {}  # phone_number -> dispatch_rule_id
        
    async def initialize(self) -> bool:
        """Initialize LiveKit API client"""
        try:
            self.api_client = api.LiveKitAPI(
                url=self.settings.livekit_url,
                api_key=self.settings.livekit_api_key,
                api_secret=self.settings.livekit_api_secret
            )
            self.logger.info("✅ LiveKit Manager initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LiveKit API: {e}")
            return False
    
    async def setup_phone_number(self, phone_number: str, agent_name: str) -> bool:
        """Setup SIP trunk and dispatch rule for a phone number"""
        try:
            # Create or get trunk
            trunk_id = await self._ensure_trunk(phone_number)
            if not trunk_id:
                return False
            
            self.trunk_ids[phone_number] = trunk_id
            
            # Create dispatch rule
            dispatch_rule_id = await self._create_dispatch_rule(phone_number, agent_name, trunk_id)
            if not dispatch_rule_id:
                return False
            
            self.dispatch_rule_ids[phone_number] = dispatch_rule_id
            
            self.logger.info(f"✅ Phone number {phone_number} setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup {phone_number}: {e}")
            return False
    
    async def _ensure_trunk(self, phone_number: str) -> Optional[str]:
        """Create or get existing trunk for phone number"""
        try:
            # List existing trunks
            request = api.ListSIPInboundTrunkRequest()
            existing_trunks = await self.api_client.sip.list_sip_inbound_trunk(request)
            
            # Check if trunk exists
            for trunk in existing_trunks.items:
                if phone_number in trunk.numbers:
                    self.logger.info(f"Found existing trunk for {phone_number}")
                    return trunk.sip_trunk_id
            
            # Create new trunk
            trunk_info = api.SIPInboundTrunkInfo(
                name=f"Persistent-{phone_number.replace('+', '')}",
                numbers=[phone_number],
                krisp_enabled=True
            )
            
            request = api.CreateSIPInboundTrunkRequest(trunk=trunk_info)
            result = await self.api_client.sip.create_sip_inbound_trunk(request)
            
            self.logger.info(f"✅ Created trunk for {phone_number}: {result.sip_trunk_id}")
            return result.sip_trunk_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create trunk for {phone_number}: {e}")
            return None
    
    async def _create_dispatch_rule(self, phone_number: str, agent_name: str, trunk_id: str) -> Optional[str]:
        """Create dispatch rule routing phone number to agent"""
        try:
            # Clean up any existing rules for this number
            await self._cleanup_existing_rules(phone_number)
            
            # Create dispatch rule
            rule = api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                    room_prefix=f"call-{phone_number.replace('+', '')}-"
                )
            )
            
            room_config = api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=agent_name,
                        metadata=f'{{"phone_number": "{phone_number}"}}'
                    )
                ]
            )
            
            dispatch_rule_info = api.SIPDispatchRuleInfo(
                name=f"Persistent-{phone_number.replace('+', '')}",
                rule=rule,
                room_config=room_config,
                trunk_ids=[trunk_id]
            )
            
            request = api.CreateSIPDispatchRuleRequest(dispatch_rule=dispatch_rule_info)
            result = await self.api_client.sip.create_sip_dispatch_rule(request)
            
            self.logger.info(f"✅ Created dispatch rule for {phone_number} -> {agent_name}")
            return result.sip_dispatch_rule_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create dispatch rule for {phone_number}: {e}")
            return None
    
    async def _cleanup_existing_rules(self, phone_number: str):
        """Remove any existing dispatch rules for this phone number"""
        try:
            request = api.ListSIPDispatchRuleRequest()
            existing_rules = await self.api_client.sip.list_sip_dispatch_rule(request)
            
            phone_digits = phone_number.replace('+', '')
            
            for rule in existing_rules.items:
                if phone_digits in (rule.name or ""):
                    try:
                        delete_req = api.DeleteSIPDispatchRuleRequest(
                            sip_dispatch_rule_id=rule.sip_dispatch_rule_id
                        )
                        await self.api_client.sip.delete_sip_dispatch_rule(delete_req)
                        self.logger.info(f"Deleted old dispatch rule: {rule.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete rule {rule.name}: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Error cleaning up rules: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all phone number setups"""
        health = {}
        try:
            for phone_number in self.settings.phone_numbers:
                # Check if trunk exists
                trunk_ok = phone_number in self.trunk_ids
                # Check if dispatch rule exists
                rule_ok = phone_number in self.dispatch_rule_ids
                health[phone_number] = trunk_ok and rule_ok
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
        return health

livekit_manager = LiveKitManager()
