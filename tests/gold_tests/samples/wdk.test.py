Test.Summary='''
Basic test for making sure WDK works
'''

Test.SkipUnless(
    Condition.IsPlatform('windows'),
     Condition.HasRegKey(
                    HKEY_LOCAL_MACHINE,
                    [r'SOFTWARE\Wow6432Node\Microsoft\KitSetup\configured-kits',
                     r'SOFTWARE\Microsoft\KitSetup\configured-kits',
                     ],
                    "WDK not installed on the system"
                   )
    )
Setup.Copy.FromSample('wdk')

Test.AddBuildRun()


