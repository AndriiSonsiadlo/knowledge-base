---
id: details-panel-customization
title: Details panel customization
sidebar_label: Details panel customization
sidebar_position: 2
tags: [ unreal-engine, ue5, c++, editor, property-editor, slate, details-panel ]
---

# Details panel customization

The default Details panel — the one every `UCLASS` and `USTRUCT` gets for free — is a generic property
grid: one row per `UPROPERTY`, laid out in declaration order, grouped by `Category`. That's the right
default and the wrong final answer for anything designers touch a lot: a struct whose fields only make
sense combined into one row, a class where changing one property should hide three others, an asset
that wants a "regenerate" button that isn't a property at all. `IDetailCustomization` and
`IPropertyTypeCustomization` are how you replace or augment that generated grid without touching the
`UCLASS`/`USTRUCT` itself.

## Why this matters

Without a customization, your only lever over how a property looks is what you can express through
`UPROPERTY` specifiers (`EditCondition`, `ClampMin`, category grouping) — which covers a lot, but not
"this row should be a color swatch with an eyedropper," "this pointer should show a live preview," or
"only show these three fields when this enum is set to a specific value, and validate them against each
other." Reach for `IDetailCustomization`/`IPropertyTypeCustomization` when the UI logic can't be
expressed as metadata on the property itself. Reaching for them too early — customizing a Details panel
just to reorder rows that `Category` and `DisplayPriority` metadata could reorder for you — is wasted
Slate code maintaining itself against every future property added to the class.

## Mental model

There are two distinct customization interfaces, registered through two distinct registration calls on
the same module, and it's easy to reach for the wrong one:

| Interface | Customizes | Registered via |
|---|---|---|
| `IDetailCustomization` | An entire class's Details panel (all properties of a `UCLASS`, as shown when that object is selected) | `FPropertyEditorModule::RegisterCustomClassLayout` |
| `IPropertyTypeCustomization` | One property *type* (a `USTRUCT`, or a specific property), wherever it appears — inside any Details panel, any struct, any array | `FPropertyEditorModule::RegisterCustomPropertyTypeLayout` |

```mermaid
flowchart TD
    Module[Your Editor module] -->|StartupModule| Get["FModuleManager::GetModuleChecked<FPropertyEditorModule>(\"PropertyEditor\")"]
    Get --> RegClass["RegisterCustomClassLayout(<br/>  ClassName,<br/>  FOnGetDetailCustomizationInstance)"]
    Get --> RegProp["RegisterCustomPropertyTypeLayout(<br/>  StructName,<br/>  FOnGetPropertyTypeCustomizationInstance)"]

    RegClass --> Detail[IDetailCustomization::CustomizeDetails]
    RegProp --> Header[IPropertyTypeCustomization::CustomizeHeader]
    RegProp --> Children[IPropertyTypeCustomization::CustomizeChildren]

    Detail -->|"rebuilds whole panel"| Panel[Details panel for one selected UObject]
    Header -->|"rebuilds one property row, wherever it appears"| Panel
```

Both paths funnel through the same module, `PropertyEditor`, which owns the Details view widget
infrastructure (`FDetailsView`, `IDetailLayoutBuilder`, and the row-building utilities both
customization interfaces use).

## The mechanics

### IDetailCustomization: whole-class layout

`IDetailCustomization::CustomizeDetails(IDetailLayoutBuilder& DetailLayout)` is the entry point — it's
called once per Details view refresh, and it receives the `IDetailLayoutBuilder` for the *entire*
selected object (or objects, if multiple are selected and share a common base class). Inside it you can
hide default-generated rows, add custom rows, reorder categories, and read/write the selected object's
properties directly.

```cpp title="MyActorDetails.h — customizes every AMyActor's Details panel"
class FMyActorDetails : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance()
    {
        return MakeShared<FMyActorDetails>();
    }

    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailLayout) override;
};
```

```cpp title="MyActorDetails.cpp"
void FMyActorDetails::CustomizeDetails(IDetailLayoutBuilder& DetailLayout)
{
    // Pull the object(s) currently shown in this Details view.
    TArray<TWeakObjectPtr<UObject>> Objects;
    DetailLayout.GetObjectsBeingCustomized(Objects);

    IDetailCategoryBuilder& Category = DetailLayout.EditCategory("Gameplay");

    // Hide a property that shouldn't show up in the default grid.
    TSharedRef<IPropertyHandle> InternalStateHandle =
        DetailLayout.GetProperty(GET_MEMBER_NAME_CHECKED(AMyActor, InternalState));
    DetailLayout.HideProperty(InternalStateHandle);

    // Add a custom row with a button that doesn't correspond to any UPROPERTY.
    Category.AddCustomRow(FText::FromString("Regenerate"))
        .NameContent()
        [
            SNew(STextBlock).Text(FText::FromString("Regenerate mesh"))
        ]
        .ValueContent()
        [
            SNew(SButton)
                .Text(FText::FromString("Regenerate"))
                .OnClicked_Lambda([Objects]() -> FReply
                {
                    for (const TWeakObjectPtr<UObject>& Obj : Objects)
                    {
                        if (AMyActor* Actor = Cast<AMyActor>(Obj.Get()))
                        {
                            Actor->RegenerateMesh();
                        }
                    }
                    return FReply::Handled();
                })
        ];
}
```

### IPropertyTypeCustomization: per-type row layout

`IPropertyTypeCustomization` customizes one property *type* — most commonly a `USTRUCT` — wherever it's
used: as a top-level property, nested inside another struct, or as an array element. It splits into two
functions per Epic's interface reference: `CustomizeHeader` customizes the property row itself (the
single-line summary shown when the row is collapsed), and `CustomizeChildren` adds child rows shown when
the row is expanded. If `CustomizeHeader` doesn't populate the row, child rows are added inline instead
of nested under a header — a documented detail worth knowing before you wonder why your struct rendered
flat.

```cpp title="FMyRangeCustomization.h — collapses {Min, Max} into one row"
class FMyRangeCustomization : public IPropertyTypeCustomization
{
public:
    static TSharedRef<IPropertyTypeCustomization> MakeInstance()
    {
        return MakeShared<FMyRangeCustomization>();
    }

    virtual void CustomizeHeader(
        TSharedRef<IPropertyHandle> StructPropertyHandle,
        FDetailWidgetRow& HeaderRow,
        IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

    virtual void CustomizeChildren(
        TSharedRef<IPropertyHandle> StructPropertyHandle,
        IDetailChildrenBuilder& StructBuilder,
        IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;
};
```

```cpp title="FMyRangeCustomization.cpp"
void FMyRangeCustomization::CustomizeHeader(
    TSharedRef<IPropertyHandle> StructPropertyHandle,
    FDetailWidgetRow& HeaderRow,
    IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
    TSharedPtr<IPropertyHandle> MinHandle =
        StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FMyRange, Min));
    TSharedPtr<IPropertyHandle> MaxHandle =
        StructPropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FMyRange, Max));

    HeaderRow
        .NameContent()
        [
            StructPropertyHandle->CreatePropertyNameWidget()
        ]
        .ValueContent()
        .MinDesiredWidth(200.f)
        [
            SNew(SHorizontalBox)
            + SHorizontalBox::Slot()
            [
                MinHandle->CreatePropertyValueWidget()
            ]
            + SHorizontalBox::Slot()
            [
                MaxHandle->CreatePropertyValueWidget()
            ]
        ];
}

void FMyRangeCustomization::CustomizeChildren(
    TSharedRef<IPropertyHandle> StructPropertyHandle,
    IDetailChildrenBuilder& StructBuilder,
    IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
    // Left empty: this customization fully replaces the row with CustomizeHeader,
    // so there are no separate expandable children.
}
```

### Registering both with FPropertyEditorModule

Registration happens in your `Editor` module's `StartupModule()`, and must be reversed in
`ShutdownModule()` — the Details panel infrastructure holds onto registered delegates, and an unloaded
module left registered is a dangling-callback crash waiting for the next Details refresh.

```cpp title="MyToolEditorModule.cpp"
void FMyToolEditorModule::StartupModule()
{
    FPropertyEditorModule& PropertyModule =
        FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");

    PropertyModule.RegisterCustomClassLayout(
        "MyActor",
        FOnGetDetailCustomizationInstance::CreateStatic(&FMyActorDetails::MakeInstance));

    PropertyModule.RegisterCustomPropertyTypeLayout(
        "MyRange",
        FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FMyRangeCustomization::MakeInstance));

    PropertyModule.NotifyCustomizationModuleChanged();
}

void FMyToolEditorModule::ShutdownModule()
{
    if (FModuleManager::Get().IsModuleLoaded("PropertyEditor"))
    {
        FPropertyEditorModule& PropertyModule =
            FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");

        PropertyModule.UnregisterCustomClassLayout("MyActor");
        PropertyModule.UnregisterCustomPropertyTypeLayout("MyRange");
        PropertyModule.NotifyCustomizationModuleChanged();
    }
}
```

Both `RegisterCustomClassLayout` and `RegisterCustomPropertyTypeLayout` take the class or struct name as
an `FName`/string (not a `UClass*`/`UScriptStruct*`), and a delegate that produces a new instance of your
customization object per Details view — `MakeInstance` is a factory function, not a singleton, because
each open Details panel gets its own customization instance.

:::note
The exact parameter list of `RegisterCustomClassLayout` (it also accepts an optional predicate for
conditional application) is long-standing, stable API but its full current signature — including any
5.x additions such as `FRegisterCustomClassLayoutParams` — was not pulled verbatim from the sources
consulted here. Check `PropertyEditorModule.h` for your engine version before assuming the exact
overload set.
:::

### Build.cs dependencies

```csharp title="MyToolEditor.Build.cs (excerpt)"
PrivateDependencyModuleNames.AddRange(new string[]
{
    "Slate",
    "SlateCore",
    "UnrealEd",
    "PropertyEditor",
    "EditorStyle",
});
```

## Gotchas

:::warning[Register in StartupModule, unregister in ShutdownModule — always both]
Skipping the `ShutdownModule` unregister is the single most common bug here: Live Coding or a plugin
disable/enable cycle unloads and reloads your module, and a stale registration left pointing at a
destroyed static function is a crash on the next Details panel refresh for that class, not an
immediate one — which makes it look unrelated to the module you just touched.
:::

:::warning[CustomizeDetails runs once per refresh, not once per object lifetime]
Don't treat `CustomizeDetails` as a constructor — it's called every time the Details view rebuilds
(selection change, undo/redo, a property edit that triggers `PostEditChangeProperty` with a layout
refresh). Expensive work inside it (asset scans, file I/O) runs on every keystroke-adjacent refresh if
you're not careful; cache what you can outside the function.
:::

:::caution[IPropertyTypeCustomization for a struct applies everywhere that struct is used]
Registering a customization for `FMyRange` changes how it renders in *every* Details panel across the
editor, not just the one class you had in mind — including inside arrays, maps, and other structs that
embed it. Confirm the struct isn't reused somewhere the new layout would be wrong before registering
globally.
:::

:::caution[Empty CustomizeChildren does not mean "no children" by accident]
If you leave `CustomizeChildren` empty because `CustomizeHeader` already shows everything, that's a
deliberate choice — but forgetting to implement it at all (rather than deliberately leaving it empty)
for a struct with more fields than fit in the header row silently drops those fields from the UI with no
error. Decide explicitly whether children should exist.
:::

## See also

- [Editor-only modules](./editor-modules.md) — the `Editor`-typed module this customization code has to
  live in.
- [Custom asset types](./custom-asset-types.md) — factories and asset type actions often pair with a
  Details customization for the asset they create.
- [Editor Utility Widgets](./editor-utility-widgets.md) — a Slate-free alternative when the tool doesn't
  need to hook into the Details panel specifically.
- [Epic — Property Editor module reference](https://dev.epicgames.com/documentation/unreal-engine/API/Editor/PropertyEditor)

