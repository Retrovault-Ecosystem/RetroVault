#version 450

#pragma parameter RVV_BRIGHTNESS "Brightness" 1.0 0.5 2.0 0.05
#pragma parameter RVV_MASK_STRENGTH "Mask strength" 0.0 0.0 0.5 0.05
#pragma parameter RVV_SCANLINE_STRENGTH "Scanline strength" 0.0 0.0 0.5 0.05

layout(push_constant) uniform Push
{
    vec4 SourceSize;
    vec4 OriginalSize;
    vec4 OutputSize;
    uint FrameCount;
    float RVV_BRIGHTNESS;
    float RVV_MASK_STRENGTH;
    float RVV_SCANLINE_STRENGTH;
} params;

// RetroArch supplies the projection/orientation for its vertex coordinates.
// Applying this matrix preserves the frontend-owned viewport.
layout(std140, set = 0, binding = 0) uniform UBO
{
    mat4 MVP;
} global;

#pragma stage vertex

layout(location = 0) in vec4 Position;
layout(location = 1) in vec2 TexCoord;

layout(location = 0) out vec2 vTexCoord;

void main()
{
    gl_Position = global.MVP * Position;
    vTexCoord = TexCoord;
}

#pragma stage fragment

layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 FragColor;

layout(set = 0, binding = 2) uniform sampler2D Source;

void main()
{
    /*
     * Geometry-neutral production foundation.
     *
     * No crop, stretch, viewport, aspect or title-specific behavior
     * belongs in this shader. Presentation geometry remains outside
     * shader authority.
     */
    vec4 color = texture(Source, vTexCoord);
    // Zero-strength defaults preserve the qualified pass-through appearance.
    float row = fract(vTexCoord.y * params.SourceSize.y);
    float scan = 1.0 - params.RVV_SCANLINE_STRENGTH * pow(sin(row * 3.14159265), 2.0);
    int column = int(gl_FragCoord.x) % 3;
    vec3 mask = vec3(1.0 - params.RVV_MASK_STRENGTH);
    mask[column] = 1.0;
    FragColor = vec4(color.rgb * params.RVV_BRIGHTNESS * scan * mask, color.a);
}
