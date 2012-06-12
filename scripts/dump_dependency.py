import sys
import os
import re
import xml.dom.minidom as minidom

import scons_setup
import cache_unpickle
import options_common

indentIncrement = '  '

def __createPropsNodeXML(document, props):
    propsNode = document.createElement('properties')
    if props is not None:
        for k, v in props.iteritems():
            propNode = document.createElement('property')
            propNode.setAttribute('key', str(k))
            if not isinstance(v, list) and not isinstance(v, tuple):
                v = [v]
            for vItem in v:
                propValNode = document.createElement('val')
                propValNode.appendChild(document.createTextNode(str(vItem)))
                propNode.appendChild(propValNode)
            propsNode.appendChild(propNode)

    return propsNode

def __dumpPartInfoXML(document, partInfo, sections, cacheFilesDir):
    partNode = document.createElement('part')
    rootNode.appendChild(partNode)

    aliasNode = document.createElement('alias')
    aliasNode.appendChild(document.createTextNode(partInfo.alias))
    partNode.appendChild(aliasNode)

    nameNode = document.createElement('name')
    nameNode.appendChild(document.createTextNode(partInfo.name))
    partNode.appendChild(nameNode)

    versionNode = document.createElement('version')
    versionNode.appendChild(document.createTextNode(partInfo.version))
    partNode.appendChild(versionNode)

    vcsNode = document.createElement('vcs')
    cacheVcsDir = os.path.join(cacheFilesDir, 'vcs')
    if os.path.exists(cacheVcsDir) and os.path.isdir(cacheVcsDir):
        partVcsCacheFile = os.path.join(cacheVcsDir, partInfo.alias) + '.cache'
        if os.path.exists(partVcsCacheFile) and os.path.isfile(partVcsCacheFile):
            storedData = cache_unpickle.unpickle(partVcsCacheFile)
            assert(isinstance(storedData, dict))

            for key in ['type', 'server']:
                if storedData.has_key(key):
                    currNode = document.createElement(key)
                    currNode.appendChild(document.createTextNode(storedData[key]))
                    vcsNode.appendChild(currNode)
    partNode.appendChild(vcsNode)

    # 'kw' field was added recently to part_info, so need to handle situation when
    # it is absent in specific cache
    partNode.appendChild(__createPropsNodeXML(document, partInfo.__dict__.get('kw')))

    for secName, secContents in partInfo.sections.iteritems():
        section = sections[secName + '::' + partInfo.alias]
        sectionNode = document.createElement('section')

        secNameNode = document.createElement('name')
        secNameNode.appendChild(document.createTextNode(section.name))
        sectionNode.appendChild(secNameNode)

        secIdNode = document.createElement('alias')
        secIdNode.appendChild(document.createTextNode(section.ID))
        sectionNode.appendChild(secIdNode)
        secDependsOnNode = document.createElement('dependsOn')
        for component in section.dependson:
            compNode = document.createElement('component')

            declaredCompNode = document.createElement('declared')
            declaredCompNameNode = document.createElement('name')
            declaredCompNameNode.appendChild(document.createTextNode(component['PartRef']))
            declaredCompNode.appendChild(declaredCompNameNode)
            compNode.appendChild(declaredCompNode)

            partCompNode = document.createElement('part')
            aliasPartCompNode = document.createElement('alias')
            partObj = component['Part']
            if partObj is not None:
                aliasPartCompNode.appendChild(document.createTextNode(partObj.ID))
            partCompNode.appendChild(aliasPartCompNode)

            sectionPartCompNode = document.createElement('section')
            sectionNamePartCompNode = document.createElement('name')
            sectionNamePartCompNode.appendChild(document.createTextNode(component['SectionName']))
            sectionPartCompNode.appendChild(sectionNamePartCompNode)
            partCompNode.appendChild(sectionPartCompNode)
            compNode.appendChild(partCompNode)

            tt = parts_target_type.target_type(component['PartRef'])
            compNode.appendChild(__createPropsNodeXML(document, tt.Properties))

            reqsCompNode = document.createElement('requires')
            for req in component['Requires']:
                reqCompNode = document.createElement('req')
                for key, val in req.Serialize().iteritems():
                    itemReqCompNode = document.createElement(key)
                    itemReqCompNode.appendChild(document.createTextNode(str(val)))
                    reqCompNode.appendChild(itemReqCompNode)
                reqsCompNode.appendChild(reqCompNode)
            compNode.appendChild(reqsCompNode)

            secDependsOnNode.appendChild(compNode)
        sectionNode.appendChild(secDependsOnNode)

        partNode.appendChild(sectionNode)

def __createPropsNodeTXT(props, indent = ''):
    return indent + str(props)

def __createPartInfoTXT(partInfo, sections, cacheFilesDir, indent = ''):
    txtOutput = ''

    if verbosity == 'low':
        depIndent = indent + indentIncrement

        for secName, secContents in partInfo.sections.iteritems():
            section = sections[secName + '::' + partInfo.alias]

            depStrs = []
            for component in section.dependson:
                partObj = component['Part']
                depStr = component['SectionName'] + '::' + partObj.ID

                tt = parts_target_type.target_type(component['PartRef'])
                for key, val in tt.Properties.iteritems():
                    depStr += '@' + key + ':'
                    if isinstance(val, list) or isinstance(val, tuple):
                        depStr += ','.join([str(item) for item in val])
                    else:
                        depStr += str(val)

                depStrs.append(depStr)

            txtOutput += indent + section.ID + '@version:' + partInfo.version
            for depStr in depStrs:
                txtOutput +=  '\n' + depIndent + depStr

        return txtOutput

    currIndent = indent
    txtOutput += currIndent + 'Part' + '\n'

    currIndent += indentIncrement
    txtOutput += currIndent + 'alias = {0}\n'.format(partInfo.alias)
    txtOutput += currIndent + 'name = {0}\n'.format(partInfo.name)
    txtOutput += currIndent + 'version = {0}\n'.format(partInfo.version)

    cacheVcsDir = os.path.join(cacheFilesDir, 'vcs')
    if os.path.exists(cacheVcsDir) and os.path.isdir(cacheVcsDir):
        partVcsCacheFile = os.path.join(cacheVcsDir, partInfo.alias) + '.cache'
        if os.path.exists(partVcsCacheFile) and os.path.isfile(partVcsCacheFile):
            storedData = cache_unpickle.unpickle(partVcsCacheFile)
            assert(isinstance(storedData, dict))

            for key in ['type', 'server']:
                if storedData.has_key(key):
                    txtOutput += currIndent + 'vcs {0} = {1}\n'.format(key, storedData[key])

    txtOutput += currIndent + 'kw = {0}\n'.format(__createPropsNodeTXT(partInfo.kw))

    for secName, secContents in partInfo.sections.iteritems():
        section = sections[secName + '::' + partInfo.alias]

        txtOutput += currIndent + 'Section' + '\n'
        currIndentSec = currIndent + indentIncrement
        txtOutput += currIndentSec + 'name = {0}\n'.format(section.name)
        txtOutput += currIndentSec + 'alias = {0}\n'.format(section.ID)

        txtOutput += currIndentSec + 'dependsOn\n'
        currIndentComp = currIndentSec + indentIncrement
        for component in section.dependson:
            txtOutput += currIndentComp + 'Component' + '\n'
            currIndentCompPart = currIndentComp + indentIncrement

            partObj = component['Part']
            txtOutput += currIndentCompPart + 'Part(alias = {0}, section name = {1})\n'.format( \
                (partObj.ID if partObj is not None else None), component['SectionName'])

            tt = parts_target_type.target_type(component['PartRef'])
            txtOutput += currIndentCompPart + 'properties = {0}\n'.format(__createPropsNodeTXT(tt.Properties))

            reqsStr = [(str(req.Serialize()) if verbosity == 'full' else req.key) for req in component['Requires']]
            separator = (' |\n' + currIndentCompPart + ' ') if verbosity == 'full' else ' | '
            txtOutput += currIndentCompPart + 'requires = {0}\n'.format(separator.join(reqsStr))

    return txtOutput

if __name__ == '__main__':
    parser = options_common.getCommonParser(str(__file__))

    outputFormats = ['txt', 'xml']
    verbosities = ['low', 'medium', 'full']

    parser.add_option('-f', '--output-format', dest = 'outputFormat',
        choices = outputFormats,
        help = 'Output format. Choices are %s. Default is "%s"' % (', '.join(outputFormats), 'xml'))

    parser.add_option('-v', '--verbosity', dest = 'verbosity',
        choices = verbosities,
        help = ('Verbosity of output. Applicable for "%s" output format.' + \
            ' Choices are %s. Default is "%s".') % ('txt', ', '.join(verbosities), 'low'))

    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.error('No path to cache file specified')
        sys.exit(1)
    elif len(args) > 1:
        print 'WARNING: Extra argument(s) {0} ignored.'.format(args[1:])

    datafile = args[0]
    if not os.path.isfile(datafile):
        parser.error('Not a valid filepath: %s' % str(datafile))
        sys.exit(1)

    outputFormat = options.outputFormat
    if outputFormat is None:
        outputFormat = 'xml'

    verbosity = options.verbosity
    if verbosity is None:
        verbosity = 'low'
    elif outputFormat != 'txt':
        print ('WARNING: ignoring verbosity since it is applicable for "%s" output format' + \
            ' and dependency information only.') % 'txt'

    (cacheRootDir, cacheDirName, cacheKey, cacheName) = cache_unpickle.split(datafile)

    if cache_unpickle.CacheFilenames.FILE_NODEINFO != cacheName:
        raise Exception('"%s" cache file does not contain dependency information' % cacheName)

    scons_setup.setup(options.sconsVersion)
    storedData = cache_unpickle.unpickle(datafile)
    assert(isinstance(storedData, dict))

    import parts.pnode.section_info as parts_pnode_section_info
    import parts.pnode.part_info as parts_pnode_part_info
    import parts.target_type as parts_target_type

    document = None
    rootNode = None
    txtOutput = None
    if outputFormat == 'xml':
        document = minidom.Document()
        rootNode = document.createElement('root')
    elif outputFormat == 'txt':
        txtOutput = ''

    includeRexes = [re.compile(i) for i in options.includeParts]
    excludeRexes = [re.compile(i) for i in options.excludeParts]

    for rootKey, rootVal in storedData.iteritems():
        if rootKey != cache_unpickle.NodeinfoKeys.KNOWN_PNODES:
            continue

        assert(isinstance(rootVal, dict))

        sections = {}
        for k, v in rootVal.iteritems():
            if isinstance(v, parts_pnode_section_info.section_info):
                if sections.has_key(k):
                    raise Exception('More than one section with key {0} found'.format(k))
                v.ID = k
                sections[k] = v
            elif isinstance(v, parts_pnode_part_info.part_info):
                continue
            else:
                raise Exception('Unknown type of pnode: {0}'.format(type(v)))

        for k, v in rootVal.iteritems():
            if any([i.search(k) for i in excludeRexes]):
                continue
            if includeRexes and not any([i.search(k) for i in includeRexes]):
                continue

            if isinstance(v, parts_pnode_section_info.section_info):
                continue
            elif isinstance(v, parts_pnode_part_info.part_info):
                cacheFilesDir = os.path.join(cacheRootDir, cacheDirName)
                if outputFormat == 'xml':
                    __dumpPartInfoXML(document, v, sections, cacheFilesDir)
                elif outputFormat == 'txt':
                    txtOutput += __createPartInfoTXT(v, sections, cacheFilesDir) + '\n'
            else:
                raise Exception('Unknown type of pnode: {0}'.format(type(v)))

    # Parts redirects stderr and stdout, need to return them back
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    if outputFormat == 'xml':
        document.appendChild(rootNode)
        print document.toprettyxml(encoding="utf-8")
    elif outputFormat == 'txt':
        print txtOutput,
