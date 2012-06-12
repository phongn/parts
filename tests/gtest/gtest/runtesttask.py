import os
import subprocess
import time

import host
from streamwriter import StreamWriter, PipeRedirector
import events.eventinfo
import testers
import setup
import conditions
import string # for Template

class RunTestTask(object):
    def __init__(self,test):
        self.__test=test

    def __call__(self):
        #make sandbox run directory for this test
        os.makedirs(self.__test.RunDirectory)
        try:
            # load the test data
            self.read_test()
            # see if we can run it
            # ie test for conditions to make sure this test can run
            if self.CanRunTest:
                #Given we can run it
                # do any setup for the test
                self.setup_test()
                # run it
                self.run_test()
                # clean up an mess
                self.clean_up_test()
            else:
                self.__test._SetResult(testers.ResultType.Skipped)
        except setup.Error:
            self.__test._SetResult(testers.ResultType.Failed)
        #return our results
        return self.__test._Result

    def read_test(self):
        #First we need to load a given test
        #host.WriteMessage('Reading Test infomation "{0}" in {1}'.format(self.__test.Name,self.__test.TestDirectory))

        # load the test data. this mean exec the data
        #create the locals we want to pass
        locals={
                'test':self.__test,
                'Test':self.__test,
                'Setup':self.__test.Setup,
                'Condition':conditions.ConditionFactory(),
                'Testers':testers,
                }

        #get full path
        file=os.path.join(self.__test.TestDirectory,self.__test.TestFile)
        exec(compile(open(file).read(), file, 'exec'),locals,locals)
        host.WriteVerbose("reading",'Done reading test "{0}"'.format(self.__test.Name))

    @property
    def CanRunTest(self):
        if not self.__test._Conditions._Passed:
            # for some reason we can't run this test
            # Look at the conditions for running this test to get the reason why we can't run.
            reason = self.__test._Conditions._Reason
            host.WriteWarning("Skipping test {0} because:\n {1}".format(self.__test.Name,reason),
                              show_stack=False)
            return False
        return True

    def setup_test(self):
        tasks=self.__test.Setup._do_setup()

    def clean_up_test(self):
        tasks=self.__test.Setup._do_cleanup()

    def run_test(self):
        host.WriteMessage("Starting test Name: {0}".format(self.__test.Name))
        skip_tests=None
        for tr in self.__test._TestRuns:
            if skip_tests:
                # we had some failure... set state on rest of tests to a Skipped state
                tr._Result=testers.ResultType.Skipped
            else:
                # run the test
                self.do_test_run(tr)
            if tr._Result == testers.ResultType.Failed:
                host.WriteVerbose("run_test",
                                  'Stopping test run for test "{0}" because test run "{1}" failed'.format(
                                               self.__test.Name,
                                               tr.Name
                                               )
                                  )
                skip_tests=tr.Name
            #host.WriteMessage(" {0} - {1}".format(tr.Name,testers.ResultType.to_string(tr._Result)))

    def do_test_run(self,test_run):
        ###basic setup
        #create a StreamWriter which will write out the stream data of the run to sorted files
        output=StreamWriter(os.path.join(self.__test.RunDirectory,"_tmp_{0}_{1}".format(self.__test.Name,test_run.Name)),test_run.Command)
        # the command line we will run. We add the RunDirectory to the start of the command 
        #to avoid having to deal with cwddir() issues
        command_line="cd {0} && {1}".format(self.__test.RunDirectory,test_run.Command)
        # subsitute the value of the string via the template engine
        # as this provide a safe cross platform $subst model.
        template = string.Template(command_line)
        command_line=template.substitute(self.__test.Env)

        # force all registered events to be bound to the event objects
        test_run._BindEvents()

        #make event info object
        #call event            
        test_run.StartingRun()

        proc = subprocess.Popen(
            command_line,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.__test.Env)
            
        # get the output stream from the process we created and redirect to files
        stdout = PipeRedirector(proc.stdout, output.WriteStdOut)
        stderr = PipeRedirector(proc.stderr, output.WriteStdErr)
        #make event info object
        #call event            
        test_run.RunStarted()
        
        running = True
        start_time=time.time()
        last_event_time=start_time
        while running:
            running=proc.poll() is None
            curr_time=time.time()
            if curr_time-last_event_time > 500:
                #make event info object
                #call event
                test_run.Running()
        
        # clean up redirectory objects for this run
        # make sure all output is written for finish event
        stdout.close()
        stderr.close()
        output.Close()        
        
        #make event info object
        event=events.eventinfo.FinishedInfo(proc.returncode,time.time()-start_time,output)
        #call event            
        test_run.RunFinished(event)

        