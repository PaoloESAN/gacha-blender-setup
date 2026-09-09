import os

bl_info = {
    "name": "Gacha Setup",
    "author": "Mken, OctavoPE, Enthralpy, PaoloESAN",
    "version": (3, 6, 2),
    "blender": (5, 2, 0),
    "location": "3D View > Sidebar > Genshin Impact / Honkai Star Rail / Zenless Zone Zero / Neverness to Everness / Wuthering Waves / Arknights: Endfield",
    "description": "An addon to streamline the character model setup process for Gacha games in Blender 5.2+",
    "warning": "",
    "doc_url": "",
    "support": "COMMUNITY",
    "category": "HoYoverse",
    "license": "GPL-3.0-or-later",
    "tracker_url": "",
}

is_test_env = (
    os.environ.get("PYTEST_VERSION") is not None
)  # This environ variable gets set when pytest is run

if is_test_env:
    pytest_version = os.environ.get("PYTEST_VERSION")
    print(f"Pytest version: {pytest_version}")
else:
    import importlib
    import os

    import bpy

    import setup_wizard.addon_updater.addon_updater_ops as addon_updater_ops
    import setup_wizard.genshin_setup_wizard
    import setup_wizard.ui.gi_ui_setup_wizard_menu
    from setup_wizard.character_rig_setup.character_rigger_operator import (
        GI_OT_RigCharacter,
        GI_OT_CharacterRiggerOperator,
        GI_OT_ApplyHairClothesPhysicsOperator,
        GI_OT_ApplyHairDressPhysicsOperator,
        ZZZ_OT_FixBoneChains,
    )
    from setup_wizard.character_rig_setup.wuwa_face_panel import (
        WW_OT_CreateFacePanel,
    )
    from setup_wizard.character_rig_setup.ake_face_rig import (
        AKE_OT_SetUpIsaacFaceRig,
    )
    from setup_wizard.character_rig_setup.character_rigger_props import (
        CharacterRiggerPropertyGroup,
        CharacterRiggerPropertyManager,
    )
    from setup_wizard.genshin_compositing_node_setup import (
        GI_OT_PostProcessingCompositingSetup,
    )
    from setup_wizard.genshin_import_character_model import (
        GI_OT_SetUpCharacter,
        HSR_OT_SetUpCharacter,
        ZZZ_OT_SetUpCharacter,
        NTE_OT_SetUpCharacter,
        WW_OT_SetUpCharacter,
        AKE_OT_SetUpCharacter,
        GI_OT_ClearPose,
        GI_OT_ReorientBones,
    )
    from setup_wizard.genshin_import_materials import (
        GI_OT_SetUpMaterials,
        HSR_OT_SetUpMaterials,
        ZZZ_OT_SetUpMaterials,
        NTE_OT_SetUpMaterials,
        NTE_OT_SetUpOutlines,
        NTE_OT_SetUpHairSpecular,
        WW_OT_SetUpMaterials,
        AKE_OT_SetUpMaterials,
        AKE_OT_SetUpOutlines,
    )

    from setup_wizard.genshin_import_outlines import (
        GI_OT_SetUpOutlines,
        HSR_OT_SetUpOutlines,
        ZZZ_OT_SetUpOutlines,
        WW_OT_SetUpOutlines,
    )
    from setup_wizard.genshin_setup_wizard import (
        GI_OT_GenshinSetupWizardUI,
        HSR_OT_HonkaiStarRailSetupWizardUI,
        ZZZ_OT_SetupWizardUI,
        NTE_OT_SetupWizardUI,
        WW_OT_WutheringWavesSetupWizardUI,
        AKE_OT_ArknightsEndfieldSetupWizardUI,
        setup_dependencies,
    )
    from setup_wizard.genshin_setup_wizard import (
        register as register_genshin_setup_wizard,
    )
    from setup_wizard.set_up_head_driver import (
        ZZZ_OT_SetUpHeadDriver,
        WW_OT_SetUpHeadDriver,
        AKE_OT_SetUpHeadDriver,
    )
    from setup_wizard.misc_operations import (
        ZZZ_OT_RenameCollectionAndRig,
        ZZZ_OT_MoveLightingPanelToCharacterCollection,
    )
    from setup_wizard.misc_final_steps import (
        GI_OT_FixTransformations,
        GI_OT_FinishSetup,
        HSR_OT_FinishSetup,
        ZZZ_OT_FinishSetup,
        NTE_OT_FinishSetup,
        NTE_OT_SetupCompositorNodes,
        WW_OT_FinishSetup,
        WW_OT_SetupCompositorNodes,
        AKE_OT_FinishSetup,
        AKE_OT_SetupCompositorNodes,
    )
    from setup_wizard.ui.ake_ui_setup_wizard_menu import (
        AKE_PT_Setup_Wizard_UI_Layout,
        AKE_PT_Basic_Setup_Wizard_UI_Layout,
        AKE_PT_Advanced_Setup_Wizard_UI_Layout,
        AKE_PT_UI_Character_Model_Menu,
        AKE_PT_UI_Materials_Menu,
        AKE_PT_UI_Outlines_Menu,
        AKE_PT_UI_Rig_Character_Menu,
        AKE_PT_UI_Finish_Setup_Menu,
        AKE_PT_Rig_Character_Settings,
        register_ake_properties,
        unregister_ake_properties,
        ake_frame_change_handler,
    )
    from setup_wizard.wuwa_operations import (
        WW_OT_ToggleAnimateMode,
        WW_OT_ToggleOutlines,
        WW_OT_ToggleHairTrans,
        WW_OT_ToggleStarMotion,
        WW_OT_ToggleAlphaTransparency,
        WW_OT_FixEyeUV,
        WW_OT_SeparateMesh,
        WW_OT_SetPerformanceMode,
        WW_OT_SetQualityMode,
        register_wuwa_properties,
        wuwa_frame_change_handler,
    )
    from setup_wizard.preferences import CharacterSetupWizardAddonPreferences
    from setup_wizard.ui.gi_ui_setup_wizard_menu import (
        GI_PT_Advanced_Setup_Wizard_UI_Layout,
        GI_PT_Basic_Setup_Wizard_UI_Layout,
        GI_PT_Setup_Wizard_UI_Layout,
        GI_PT_UI_Character_Model_Menu,
        GI_PT_UI_Character_Rig_Setup_Menu,
        GI_PT_UI_Finish_Setup_Menu,
        GI_PT_UI_Materials_Menu,
        GI_PT_UI_Outlines_Menu,
        GI_PT_UI_Post_Processing_Node_Editor_Setup_Menu,
        GI_PT_UI_Post_Processing_Setup_Menu,
        GI_PT_Rig_Character_Settings,
        register_gi_properties,
        unregister_gi_properties,
        gi_frame_change_handler,
        UI_Properties,
    )
    from setup_wizard.ui.hsr_ui_setup_wizard_menu import (
        HSR_PT_Advanced_Setup_Wizard_UI_Layout,
        HSR_PT_Basic_Setup_Wizard_UI_Layout,
        HSR_PT_Setup_Wizard_UI_Layout,
        HSR_PT_UI_Character_Model_Menu,
        HSR_PT_UI_Character_Rig_Setup_Menu,
        HSR_PT_UI_Finish_Setup_Menu,
        HSR_PT_UI_Materials_Menu,
        HSR_PT_UI_Outlines_Menu,
        HSR_PT_Rig_Character_Settings,
        register_hsr_properties,
        unregister_hsr_properties,
    )
    from setup_wizard.ui.nte_ui_setup_wizard_menu import (
        NTE_PT_Setup_Wizard_UI_Layout,
        NTE_PT_Basic_Setup_Wizard_UI_Layout,
        NTE_PT_Advanced_Setup_Wizard_UI_Layout,
        NTE_PT_UI_Character_Model_Menu,
        NTE_PT_UI_Materials_Menu,
        NTE_PT_UI_Outlines_Menu,
        NTE_PT_UI_Rig_Character_Menu,
        NTE_PT_UI_Finish_Setup_Menu,
    )
    from setup_wizard.ui.wuwa_ui_setup_wizard_menu import (
        WW_PT_Setup_Wizard_UI_Layout,
        WW_PT_Basic_Setup_Wizard_UI_Layout,
        WW_PT_Advanced_Setup_Wizard_UI_Layout,
        WW_PT_UI_Character_Model_Menu,
        WW_PT_UI_Materials_Menu,
        WW_PT_UI_Outlines_Menu,
        WW_PT_UI_Rig_Character_Menu,
        WW_PT_UI_Finish_Setup_Menu,
        WW_PT_Rig_Character_Settings,
    )
    from setup_wizard.ui.unified_ui_setup_wizard_menu import (
        CSW_PT_Updater_UI_Layout,
        CSW_PT_Unified_Character_Setup_Wizard_UI_Layout,
    )

    # HSR_PT_UI_Compositing_Panel_Post_Processing_UI_Layout
    from setup_wizard.ui.zzz_ui_setup_wizard_menu import (
        ZZZ_PT_Advanced_Setup_Wizard_UI_Layout,
        ZZZ_PT_Basic_Setup_Wizard_UI_Layout,
        ZZZ_PT_Setup_Wizard_UI_Layout,
        ZZZ_PT_UI_Character_Model_Menu,
        ZZZ_PT_UI_Character_Rig_Setup_Menu,
        ZZZ_PT_UI_Finish_Setup_Menu,
        ZZZ_PT_UI_Materials_Menu,
        ZZZ_PT_UI_Outlines_Menu,
        ZZZ_PT_Rig_Character_Settings,
        register_zzz_properties,
        unregister_zzz_properties,
    )

    setup_dependencies()

    modules = [
        setup_wizard.ui.gi_ui_setup_wizard_menu,
        setup_wizard.ui.hsr_ui_setup_wizard_menu,
        setup_wizard.ui.zzz_ui_setup_wizard_menu,
        setup_wizard.ui.nte_ui_setup_wizard_menu,
        setup_wizard.ui.wuwa_ui_setup_wizard_menu,
        setup_wizard.ui.ake_ui_setup_wizard_menu,
        setup_wizard.genshin_setup_wizard,
        addon_updater_ops,
    ]

    classes = [
        CharacterRiggerPropertyGroup,
        CharacterRiggerPropertyManager,
        CharacterSetupWizardAddonPreferences,
        CSW_PT_Updater_UI_Layout,
        CSW_PT_Unified_Character_Setup_Wizard_UI_Layout,
        GI_PT_Setup_Wizard_UI_Layout,
        GI_PT_Basic_Setup_Wizard_UI_Layout,
        GI_PT_Advanced_Setup_Wizard_UI_Layout,
        GI_PT_UI_Character_Model_Menu,
        GI_PT_UI_Materials_Menu,
        GI_PT_UI_Outlines_Menu,
        GI_PT_UI_Finish_Setup_Menu,
        GI_PT_UI_Character_Rig_Setup_Menu,
        GI_PT_Rig_Character_Settings,
        GI_PT_UI_Post_Processing_Setup_Menu,
        GI_PT_UI_Post_Processing_Node_Editor_Setup_Menu,
        GI_OT_GenshinSetupWizardUI,
        GI_OT_SetUpCharacter,
        GI_OT_ClearPose,
        GI_OT_ReorientBones,
        GI_OT_SetUpMaterials,
        GI_OT_SetUpOutlines,
        GI_OT_FixTransformations,
        GI_OT_FinishSetup,
        GI_OT_RigCharacter,
        GI_OT_CharacterRiggerOperator,
        GI_OT_ApplyHairClothesPhysicsOperator,
        GI_OT_ApplyHairDressPhysicsOperator,
        GI_OT_PostProcessingCompositingSetup,
        HSR_PT_Setup_Wizard_UI_Layout,
        HSR_PT_Basic_Setup_Wizard_UI_Layout,
        HSR_PT_Advanced_Setup_Wizard_UI_Layout,
        HSR_PT_UI_Character_Model_Menu,
        HSR_PT_UI_Materials_Menu,
        HSR_PT_UI_Outlines_Menu,
        HSR_PT_UI_Finish_Setup_Menu,
        HSR_PT_UI_Character_Rig_Setup_Menu,
        HSR_PT_Rig_Character_Settings,
        # HSR_PT_UI_Compositing_Panel_Post_Processing_UI_Layout,
        HSR_OT_HonkaiStarRailSetupWizardUI,
        HSR_OT_SetUpCharacter,
        HSR_OT_SetUpMaterials,
        HSR_OT_SetUpOutlines,
        HSR_OT_FinishSetup,
        ZZZ_PT_Setup_Wizard_UI_Layout,
        ZZZ_PT_Basic_Setup_Wizard_UI_Layout,
        ZZZ_PT_Advanced_Setup_Wizard_UI_Layout,
        ZZZ_PT_UI_Character_Model_Menu,
        ZZZ_PT_UI_Materials_Menu,
        ZZZ_PT_UI_Outlines_Menu,
        ZZZ_PT_UI_Character_Rig_Setup_Menu,
        ZZZ_PT_UI_Finish_Setup_Menu,
        ZZZ_PT_Rig_Character_Settings,
        ZZZ_OT_SetupWizardUI,
        ZZZ_OT_SetUpCharacter,
        ZZZ_OT_SetUpMaterials,
        ZZZ_OT_SetUpOutlines,
        ZZZ_OT_FinishSetup,
        ZZZ_OT_FixBoneChains,
        ZZZ_OT_SetUpHeadDriver,
        ZZZ_OT_RenameCollectionAndRig,
        ZZZ_OT_MoveLightingPanelToCharacterCollection,
        NTE_PT_Setup_Wizard_UI_Layout,
        NTE_PT_Basic_Setup_Wizard_UI_Layout,
        NTE_PT_Advanced_Setup_Wizard_UI_Layout,
        NTE_PT_UI_Character_Model_Menu,
        NTE_PT_UI_Materials_Menu,
        NTE_PT_UI_Outlines_Menu,
        NTE_PT_UI_Rig_Character_Menu,
        NTE_PT_UI_Finish_Setup_Menu,
        NTE_OT_SetupWizardUI,
        NTE_OT_SetUpCharacter,
        NTE_OT_SetUpMaterials,
        NTE_OT_SetUpOutlines,
        NTE_OT_SetUpHairSpecular,
        NTE_OT_SetupCompositorNodes,
        NTE_OT_FinishSetup,
        # Wuthering Waves (Gustling Waters)
        WW_PT_Setup_Wizard_UI_Layout,
        WW_PT_Basic_Setup_Wizard_UI_Layout,
        WW_PT_Advanced_Setup_Wizard_UI_Layout,
        WW_PT_UI_Character_Model_Menu,
        WW_PT_UI_Materials_Menu,
        WW_PT_UI_Outlines_Menu,
        WW_PT_UI_Rig_Character_Menu,
        WW_PT_UI_Finish_Setup_Menu,
        WW_PT_Rig_Character_Settings,
        WW_OT_WutheringWavesSetupWizardUI,
        WW_OT_SetUpCharacter,
        WW_OT_SetUpMaterials,
        WW_OT_SetUpOutlines,
        WW_OT_SetUpHeadDriver,
        WW_OT_FinishSetup,
        WW_OT_SetupCompositorNodes,
        WW_OT_CreateFacePanel,
        WW_OT_ToggleAnimateMode,
        WW_OT_ToggleOutlines,
        WW_OT_ToggleHairTrans,
        WW_OT_ToggleStarMotion,
        WW_OT_ToggleAlphaTransparency,
        WW_OT_FixEyeUV,
        WW_OT_SeparateMesh,
        WW_OT_SetPerformanceMode,
        WW_OT_SetQualityMode,
        # Arknights: Endfield
        AKE_PT_Setup_Wizard_UI_Layout,
        AKE_PT_Basic_Setup_Wizard_UI_Layout,
        AKE_PT_Advanced_Setup_Wizard_UI_Layout,
        AKE_PT_UI_Character_Model_Menu,
        AKE_PT_UI_Materials_Menu,
        AKE_PT_UI_Outlines_Menu,
        AKE_PT_UI_Rig_Character_Menu,
        AKE_PT_UI_Finish_Setup_Menu,
        AKE_PT_Rig_Character_Settings,
        AKE_OT_ArknightsEndfieldSetupWizardUI,
        AKE_OT_SetUpCharacter,
        AKE_OT_SetUpMaterials,
        AKE_OT_SetUpOutlines,
        AKE_OT_FinishSetup,
        AKE_OT_SetupCompositorNodes,
        AKE_OT_SetUpIsaacFaceRig,
    ]

    for module in modules:
        try:
            importlib.reload(module)
        except ModuleNotFoundError:
            pass  # likely new class

    _register_classes, _unregister_classes = bpy.utils.register_classes_factory(classes)
    UI_Properties.create_custom_ui_properties()


    def register():
        try:
            register_genshin_setup_wizard()
        except Exception:
            pass
        for cls in classes:
            try:
                bpy.utils.register_class(cls)
            except ValueError:
                pass
            except Exception as e:
                print(f"[GACHA SETUP] Notice registering {cls}: {e}")
        for cls_name in dir(bpy.types):
            if cls_name.startswith("VIEW3D_PT_"):
                cls_prop = getattr(bpy.types, cls_name, None)
                if cls_prop and getattr(cls_prop, "bl_category", "") == "Item" and getattr(cls_prop, "bl_label", "") in ["Properties", "Context Properties"]:
                    try:
                        bpy.utils.unregister_class(cls_prop)
                        cls_prop.bl_order = 4
                        cls_prop.bl_options = {'DEFAULT_CLOSED'}
                        bpy.utils.register_class(cls_prop)
                    except Exception:
                        pass
        register_wuwa_properties()
        register_zzz_properties()
        register_hsr_properties()
        register_gi_properties()
        register_ake_properties()
        if wuwa_frame_change_handler not in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.append(wuwa_frame_change_handler)
        if gi_frame_change_handler not in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.append(gi_frame_change_handler)
        if ake_frame_change_handler not in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.append(ake_frame_change_handler)
        addon_updater_ops.register(bl_info)


    def unregister():
        if gi_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(gi_frame_change_handler)
        if gi_frame_change_handler in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(gi_frame_change_handler)
        if wuwa_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(wuwa_frame_change_handler)
        if wuwa_frame_change_handler in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(wuwa_frame_change_handler)
        if ake_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(ake_frame_change_handler)
        if ake_frame_change_handler in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(ake_frame_change_handler)
        addon_updater_ops.unregister()
        unregister_gi_properties()
        unregister_hsr_properties()
        unregister_zzz_properties()
        unregister_ake_properties()
        try:
            setup_wizard.genshin_setup_wizard.unregister()
        except Exception:
            pass
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass

    """
    For auto_loading, but right now we're doing simple loading to have
    direct control for the order of class registration.
    """
    """
    # from setup_wizard import auto_load
    # auto_load.init()


    # def register():
    #     # auto_load.register()


    # def unregister():
    #     # auto_load.unregister()
    """
